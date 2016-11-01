// Public Domain (-) 2016 The GitFund Authors.
// See the GitFund UNLICENSE file for details.

package web

import (
	"crypto/subtle"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"reflect"
	"sync"

	"github.com/tav/gitfund/app/config"
	"google.golang.org/cloud/pubsub"
)

var (
	ctxType   = reflect.TypeOf(&Context{})
	errorType = reflect.TypeOf((*error)(nil)).Elem()
)

var (
	errMissingBody    = errors.New("missing POST body")
	errMissingData    = errors.New("empty message data in the JSON payload")
	errMissingMessage = errors.New("missing element 'message' from the JSON payload")
	errMissingWorker  = errors.New("missing worker name from the JSON payload")
)

var (
	queueTopics  = map[string]*pubsub.Topic{}
	workerTopics = map[string]*pubsub.Topic{}
)

type pushMessage struct {
	Attributes map[string]string `json:"attributes"`
	Data       string            `json:"data"`
	MessageID  string            `json:"message_id"`
}

type pushPayload struct {
	Message      *pushMessage `json:"message"`
	Subscription string       `json:"subscription"`
}

type queueData struct {
	Worker string
	Args   []interface{}
}

type queueRequest struct {
	Worker string
	Args   []*json.RawMessage
}

type Worker struct {
	Queue    *config.Queue
	Handler  interface{}
	argTypes []reflect.Type
	handler  reflect.Value
	mu       sync.Mutex
	retError bool
}

func equal(k1 string, k2 string) bool {
	return len(k1) == len(k2) && subtle.ConstantTimeCompare([]byte(k1), []byte(k2)) == 1
}

func equalBytes(k1 []byte, k2 []byte) bool {
	return len(k1) == len(k2) && subtle.ConstantTimeCompare(k1, k2) == 1
}

// _queues/handle/<queue-name>/<queue-key>
func (d *Dispatcher) callWorker(c *Context, queue string, key string) (bool, error) {
	if c.request.Body == nil {
		return false, errMissingBody
	}
	payload := &pushPayload{}
	dec := json.NewDecoder(c.request.Body)
	err := dec.Decode(payload)
	if err != nil {
		return false, err
	}
	if payload.Message == nil {
		return false, errMissingMessage
	}
	if payload.Message.Data == "" {
		return false, errMissingData
	}
	raw, err := base64.StdEncoding.DecodeString(payload.Message.Data)
	if err != nil {
		return false, err
	}
	req := &queueRequest{}
	err = json.Unmarshal(raw, req)
	if err != nil {
		return false, err
	}
	if req.Worker == "" {
		return false, errMissingWorker
	}
	worker, exists := d.Workers[req.Worker]
	if !exists {
		return false, fmt.Errorf("worker %q not specified in the dispatcher config", req.Worker)
	}
	if worker.Queue.Name != queue {
		return false, fmt.Errorf("%q queue specified for %q worker does not match called queue %q",
			worker.Queue.Name, req.Worker, queue)
	}
	qkey, err := hex.DecodeString(key)
	if err != nil {
		return false, err
	}
	if !equalBytes(worker.Queue.Key, qkey) {
		return false, fmt.Errorf("invalid key for %q worker in queue %q",
			req.Worker, worker.Queue.Name)
	}
	worker.mu.Lock()
	argTypes := worker.argTypes
	if argTypes == nil {
		rv := reflect.ValueOf(worker.Handler)
		rt := rv.Type()
		// Ensure that the handler is a function.
		if rt.Kind() != reflect.Func {
			worker.mu.Unlock()
			return false, fmt.Errorf("handler for %q worker needs to be a function, not %s",
				req.Worker, rt.Kind())
		}
		// Ensure that any return value is only an optional error.
		switch rt.NumOut() {
		case 0:
			worker.retError = false
		case 1:
			ret := rt.Out(0)
			if ret != errorType {
				worker.mu.Unlock()
				return false, fmt.Errorf(
					"the return value for the %q handler may only be an error, not %s",
					req.Worker, ret.Kind())
			}
		default:
			worker.mu.Unlock()
			return false, fmt.Errorf(
				"invalid return values for the %q handler; it may only be an error value",
				req.Worker)
		}
		// Ensure *web.Context is the first parameter.
		in := rt.NumIn()
		if in == 0 {
			worker.mu.Unlock()
			return false, fmt.Errorf(
				"missing *web.Context first parameter for the %q handler", req.Worker)
		}
		if rt.In(0) != ctxType {
			worker.mu.Unlock()
			return false, fmt.Errorf(
				"first parameter of the %q handler needs to be *web.Context, not %s", req.Worker, rt.In(0))
		}
		argTypes = make([]reflect.Type, in-1)
		for i := 1; i < in; i++ {
			argTypes[i-1] = rt.In(i)
		}
		worker.argTypes = argTypes
		worker.handler = rv
		worker.mu.Unlock()
	}
	if len(argTypes) != len(req.Args) {
		return false, fmt.Errorf("expected %d payload parameter(s) for the %q handler, got %d",
			len(argTypes), req.Worker, len(req.Args))
	}
	// TODO(tav): Should ideally take into account the time it took to get here.
	c.withTimeout(worker.Queue.Timeout)
	args := make([]reflect.Value, len(argTypes)+1)
	args[0] = reflect.ValueOf(c)
	for i, arg := range req.Args {
		typ := argTypes[i]
		isPtr := typ.Kind() == reflect.Ptr
		var rv reflect.Value
		if isPtr {
			rv = reflect.New(typ.Elem())
		} else {
			rv = reflect.New(typ)
		}
		if err = json.Unmarshal(*arg, rv.Interface()); err != nil {
			return false, fmt.Errorf("couldn't decode payload parameter %d for the %q handler: %s",
				i, req.Worker, err)
		}
		if !isPtr {
			rv = rv.Elem()
		}
		args[i+1] = rv
	}
	resp := worker.handler.Call(args)
	if worker.retError {
		return false, resp[0].Interface().(error)
	}
	return false, nil
}

// _queues/init/<init-key>
func (d *Dispatcher) initQueues(c *Context, key string) error {
	if !equal(key, config.QueueInitKey) {
		c.serve404()
		return nil
	}
	c.withTimeout(config.QueueInitTimeout)
	var url string
	if DevServer {
		url = "http://localhost:" + ServerPort + d.Path
	} else if config.CanonicalHost != "" {
		url = "https://" + config.CanonicalHost + d.Path
	} else {
		url = "https://" + config.AppID + ".appspot.com" + d.Path
	}
	if url[len(url)-1] != '/' {
		url += "/"
	}
	url += "_queues/handle"
	for _, queue := range d.Queues {
		topic := config.PubsubClient.Topic("queue." + queue.Name)
		exists, err := topic.Exists(c)
		if err != nil {
			return err
		}
		if !exists {
			_, err = config.PubsubClient.NewTopic(c, "queue."+queue.Name)
			if err != nil {
				return err
			}
		}
		sub := config.PubsubClient.Subscription("worker." + queue.Name)
		exists, err = sub.Exists(c)
		if err != nil {
			return err
		}
		endpoint := fmt.Sprintf("%s/%s/%x", url, queue.Name, queue.Key)
		if exists {
			cfg, err := sub.Config(c)
			if err != nil {
				return err
			}
			if cfg.PushConfig.Endpoint != endpoint {
				err = sub.ModifyPushConfig(c, &pubsub.PushConfig{Endpoint: endpoint})
				if err != nil {
					return err
				}
			}
		} else {
			_, err = config.PubsubClient.NewSubscription(
				c, "worker."+queue.Name, topic, queue.Timeout,
				&pubsub.PushConfig{Endpoint: endpoint})
			if err != nil {
				return err
			}
		}
	}
	return nil
}
