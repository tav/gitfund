// Public Domain (-) 2016 The GitFund Authors.
// See the GitFund UNLICENSE file for details.

package web

import (
	"bytes"
	"context"
	"crypto/hmac"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"mime"
	"mime/multipart"
	"net/http"
	"net/url"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/bradfitz/gomemcache/memcache"
	"github.com/tav/gitfund/app/config"
	"github.com/tav/gitfund/app/model"
	"github.com/tav/gitfund/app/token"
	"github.com/tav/golly/log"
	"google.golang.org/cloud/datastore"
)

// Ensure that our Context implements the interface defined by the context
// package.
var _ context.Context = (*Context)(nil)

var cookieExpire, _ = time.Parse(http.TimeFormat, "Fri, 31 Dec 99 23:59:59 GMT")

type Context struct {
	bools    map[string]bool
	buffer   *bytes.Buffer
	cookies  []string
	children map[*Context]struct{}
	deadline time.Time
	done     chan struct{}
	err      error
	files    map[string][]*multipart.FileHeader
	headers  map[string]string
	ints     map[string]int64
	mu       sync.Mutex
	output   []byte
	parent   *Context
	parsed   bool
	pathArgs []string
	pending  []*model.Key
	request  *http.Request
	status   int
	strings  map[string]string
	timer    *time.Timer
	txn      *datastore.Transaction
	user     *model.User
	userID   int64
	xsrf     string
	values   url.Values
	written  bool
}

func (c *Context) AllocateIDs(keys []*model.Key) ([]*model.Key, error) {
	dkeys := make([]*datastore.Key, len(keys))
	for idx, key := range keys {
		dkeys[idx] = key.Datastore
	}
	ctx := c.WithTimeout(config.DatastoreTimeout)
	rkeys, err := config.DataClient.AllocateIDs(c, dkeys)
	if err != nil {
		ctx.Cancel()
		return nil, err
	}
	akeys := make([]*model.Key, len(rkeys))
	for idx, key := range rkeys {
		akeys[idx] = &model.Key{Datastore: key}
	}
	ctx.Cancel()
	return akeys, nil
}

func (c *Context) BoolField(name string) bool {
	if c.parent != nil {
		return c.parent.BoolField(name)
	}
	c.ParseFields()
	if c.values.Get(name) == "" {
		return false
	}
	return true
}

func (c *Context) CacheCAS(item *memcache.Item) error {
	return config.CacheClient.CompareAndSwap(item)
}

func (c *Context) CacheDecrement(key string, delta uint64) (uint64, error) {
	return config.CacheClient.Decrement(key, delta)
}

func (c *Context) CacheDelete(key string) {
	err := config.CacheClient.Delete(key)
	if err != nil {
		c.Errorf("memcache: unexpected error in deleting key %s: %s", key, err)
	}
}

func (c *Context) CacheGet(key string) ([]byte, bool) {
	item, err := config.CacheClient.Get(key)
	if err != nil {
		if err != memcache.ErrCacheMiss {
			c.Errorf("memcache: unexpected error in getting key %s: %s", key, err)
		}
		return nil, false
	}
	return item.Value, true
}

func (c *Context) CacheGetItem(key string) (*memcache.Item, error) {
	return config.CacheClient.Get(key)
}

func (c *Context) CacheGetMulti(keys ...string) map[string][]byte {
	items, err := config.CacheClient.GetMulti(keys)
	resp := map[string][]byte{}
	if err != nil {
		c.Errorf("memcache: unexpected error in getting multi keys %s: %s", keys, err)
		return resp
	}
	for key, item := range items {
		resp[key] = item.Value
	}
	return resp
}

func (c *Context) CacheIncrement(key string, delta uint64) (uint64, error) {
	return config.CacheClient.Increment(key, delta)
}

func (c *Context) CacheSet(key string, value []byte) {
	err := config.CacheClient.Set(&memcache.Item{
		Key:        key,
		Value:      value,
		Expiration: config.MemcacheExpiration,
	})
	if err != nil {
		c.Errorf("memcache: unexpected error in setting key %s: %s", key, err)
	}
}

// Adapted from the context package in the standard library.
func (c *Context) cancel(removeFromParent bool, err error) {
	c.mu.Lock()
	if c.err != nil {
		c.mu.Unlock()
		return // already canceled
	}
	c.err = err
	close(c.done)
	for child := range c.children {
		child.cancel(false, err)
	}
	c.children = nil
	if c.timer != nil {
		c.timer.Stop()
	}
	c.mu.Unlock()
	if removeFromParent {
		p := c.parent
		if p != nil {
			p.mu.Lock()
			if p.children != nil {
				delete(p.children, c)
			}
			p.mu.Unlock()
		}
	}
}

func (c *Context) Cancel() {
	c.cancel(true, context.Canceled)
}

func (c *Context) ClearResponseHeaders() {
	if c.parent != nil {
		c.parent.ClearResponseHeaders()
		return
	}
	c.cookies = nil
	c.headers = nil
}

func (c *Context) dataSavePendingKey(key *model.Key) {
	if c.txn != nil {
		c.pending = append(c.pending, key)
		return
	}
	c.parent.dataSavePendingKey(key)
}

func (c *Context) dataTxn() *datastore.Transaction {
	if c.txn != nil {
		return c.txn
	}
	if c.parent != nil {
		return c.parent.dataTxn()
	}
	return nil
}

func (c *Context) DataGet(key *model.Key, dst interface{}) error {
	if txn := c.dataTxn(); txn != nil {
		return txn.Get(key.Datastore, dst)
	}
	ctx := c.WithTimeout(config.DatastoreTimeout)
	err := config.DataClient.Get(ctx, key.Datastore, dst)
	ctx.Cancel()
	return err
}

func (c *Context) DataGetMulti(keys []*model.Key, dst interface{}) error {
	dkeys := make([]*datastore.Key, len(keys))
	for idx, key := range keys {
		dkeys[idx] = key.Datastore
	}
	if txn := c.dataTxn(); txn != nil {
		return txn.GetMulti(dkeys, dst)
	}
	ctx := c.WithTimeout(config.DatastoreTimeout)
	err := config.DataClient.GetMulti(ctx, dkeys, dst)
	ctx.Cancel()
	return err
}

func (c *Context) DataDelete(key *model.Key) error {
	if txn := c.dataTxn(); txn != nil {
		return txn.Delete(key.Datastore)
	}
	ctx := c.WithTimeout(config.DatastoreTimeout)
	err := config.DataClient.Delete(ctx, key.Datastore)
	ctx.Cancel()
	return err
}

func (c *Context) DataDeleteMulti(keys []*model.Key) error {
	dkeys := make([]*datastore.Key, len(keys))
	for idx, key := range keys {
		dkeys[idx] = key.Datastore
	}
	if txn := c.dataTxn(); txn != nil {
		return txn.DeleteMulti(dkeys)
	}
	ctx := c.WithTimeout(config.DatastoreTimeout)
	err := config.DataClient.DeleteMulti(ctx, dkeys)
	ctx.Cancel()
	return err
}

func (c *Context) DataPut(key *model.Key, value interface{}) error {
	if txn := c.dataTxn(); txn != nil {
		pending, err := txn.Put(key.Datastore, value)
		if err != nil {
			return err
		}
		if key.Incomplete() {
			key.Pending = pending
			c.dataSavePendingKey(key)
		}
		return nil
	}
	ctx := c.WithTimeout(config.DatastoreTimeout)
	k, err := config.DataClient.Put(ctx, key.Datastore, value)
	ctx.Cancel()
	if err != nil {
		return err
	}
	if key.Incomplete() {
		key.Datastore = k
	}
	return nil
}

func (c *Context) DataPutMulti(keys []*model.Key, value interface{}) error {
	dkeys := make([]*datastore.Key, len(keys))
	for idx, key := range keys {
		dkeys[idx] = key.Datastore
	}
	if txn := c.dataTxn(); txn != nil {
		pkeys, err := txn.PutMulti(dkeys, value)
		if err != nil {
			return err
		}
		for idx, key := range keys {
			if key.Incomplete() {
				key.Pending = pkeys[idx]
				c.dataSavePendingKey(key)
			}
		}
		return nil
	}
	ctx := c.WithTimeout(config.DatastoreTimeout)
	rkeys, err := config.DataClient.PutMulti(c, dkeys, value)
	ctx.Cancel()
	if err != nil {
		return err
	}
	for idx, key := range keys {
		if key.Incomplete() {
			key.Datastore = rkeys[idx]
		}
	}
	return nil
}

func (c *Context) Deadline() (time.Time, bool) {
	return c.deadline, !c.deadline.IsZero()
}

func (c *Context) DecodeJSON(v interface{}) error {
	if c.parent != nil {
		return c.parent.DecodeJSON(v)
	}
	ct, _, _ := mime.ParseMediaType(c.request.Header.Get("Content-Type"))
	if ct != "application/json" {
		return fmt.Errorf("web: unsupported content type for decoding JSON: %s", ct)
	}
	return json.NewDecoder(c.request.Body).Decode(v)
}

func (c *Context) Debugf(format string, args ...interface{}) {
	log.Debugf(format, args...)
}

func (c *Context) DirectOutput(o []byte) {
	if c.parent != nil {
		c.parent.DirectOutput(o)
		return
	}
	c.output = o
	c.written = true
}

func (c *Context) Done() <-chan struct{} {
	return c.done
}

func (c *Context) EncodeJSON(v interface{}) {
	if c.parent != nil {
		c.parent.EncodeJSON(v)
		return
	}
	c.SetResponseHeader("Content-Type", "application/json")
	enc := json.NewEncoder(c.buffer)
	err := enc.Encode(v)
	if err != nil {
		panic(err)
	}
}

func (c *Context) Err() error {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.err
}

func (c *Context) Errorf(format string, args ...interface{}) {
	log.Errorf(format, args...)
}

func (c *Context) ExpireCookie(name string) {
	if c.parent != nil {
		c.parent.ExpireCookie(name)
		return
	}
	cookie := &http.Cookie{
		Name:     name,
		Expires:  cookieExpire,
		HttpOnly: true,
		MaxAge:   -1,
	}
	if !DevServer {
		cookie.Secure = true
	}
	c.cookies = append(c.cookies, cookie.String())
}

func (c *Context) FileField(name string) (multipart.File, *multipart.FileHeader, error) {
	if c.parent != nil {
		return c.parent.FileField(name)
	}
	c.ParseFields()
	if c.files != nil {
		if files := c.files[name]; len(files) > 0 {
			f, err := files[0].Open()
			return f, files[0], err
		}
	}
	return nil, nil, http.ErrMissingFile
}

func (c *Context) GetBool(key string) bool {
	if c.parent != nil {
		return c.parent.GetBool(key)
	}
	return c.bools[key]
}

func (c *Context) GetCookie(name string) string {
	if c.parent != nil {
		return c.parent.GetCookie(name)
	}
	cookie, err := c.request.Cookie(name)
	if err != nil {
		return ""
	}
	return c.ParseSecureToken("cookie/"+name, cookie.Value)
}

func (c *Context) GetInt(key string) int64 {
	if c.parent != nil {
		return c.parent.GetInt(key)
	}
	return c.ints[key]
}

func (c *Context) GetPathArgs() []string {
	if c.parent != nil {
		return c.parent.GetPathArgs()
	}
	return c.pathArgs
}

func (c *Context) GetString(key string) string {
	if c.parent != nil {
		return c.parent.GetString(key)
	}
	return c.strings[key]
}

func (c *Context) Infof(format string, args ...interface{}) {
	log.Infof(format, args...)
}

func (c *Context) IntField(name string) int64 {
	if c.parent != nil {
		return c.parent.IntField(name)
	}
	c.ParseFields()
	val := c.values.Get(name)
	if val == "" {
		return 0
	}
	v, err := strconv.ParseInt(val, 10, 64)
	if err != nil {
		return 0
	}
	return v
}

func (c *Context) IsCronRequest() bool {
	if c.parent != nil {
		return c.parent.IsCronRequest()
	}
	return c.request.Header.Get("X-AppEngine-Cron") != "" || DevServer
}

func (c *Context) KeyForID(kind string, id int64, parent ...*model.Key) *model.Key {
	var p *datastore.Key
	if len(parent) == 1 {
		p = parent[0].Datastore
	} else if len(parent) > 1 {
		panic(fmt.Errorf("web: multiple parent keys specified in place of optional parent key: %s", parent))
	}
	return &model.Key{Datastore: datastore.NewKey(c, kind, "", id, p)}
}

func (c *Context) KeyForName(kind string, name string, parent ...*model.Key) *model.Key {
	var p *datastore.Key
	if len(parent) == 1 {
		p = parent[0].Datastore
	} else if len(parent) > 1 {
		panic(fmt.Errorf("web: multiple parent keys specified in place of optional parent key: %s", parent))
	}
	return &model.Key{Datastore: datastore.NewKey(c, kind, name, 0, p)}
}

func (c *Context) NewKey(kind string, parent ...*model.Key) *model.Key {
	var p *datastore.Key
	if len(parent) == 1 {
		p = parent[0].Datastore
	} else if len(parent) > 1 {
		panic(fmt.Errorf("web: multiple parent keys specified in place of optional parent key: %s", parent))
	}
	return &model.Key{Datastore: datastore.NewKey(c, kind, "", 0, p)}
}

func (c *Context) parsePostBody(r *http.Request) string {
	if r.Body == nil {
		return "missing POST body"
	}
	ct := r.Header.Get("Content-Type")
	if ct == "" {
		return "missing POST content-type"
	}
	mt, params, err := mime.ParseMediaType(ct)
	if err != nil {
		return err.Error()
	}
	switch mt {
	case "application/x-www-form-urlencoded":
		body, err := ioutil.ReadAll(r.Body)
		if err != nil {
			return err.Error()
		}
		m, err := url.ParseQuery(string(body))
		if err != nil {
			return err.Error()
		}
		for k, v := range m {
			c.values[k] = append(c.values[k], v...)
		}
	case "multipart/form-data":
		boundary, ok := params["boundary"]
		if !ok {
			return http.ErrMissingBoundary.Error()
		}
		mr := multipart.NewReader(r.Body, boundary)
		f, err := mr.ReadForm(32 << 20)
		if err != nil {
			return err.Error()
		}
		for k, v := range f.Value {
			c.values[k] = append(c.values[k], v...)
		}
		c.files = f.File
	case "application/json":
		// Handled explicitly or by using the utility DecodeJSON method.
	case "application/octet-stream":
		// Handled explicitly.
	default:
		return fmt.Sprintf("unsupported POST content-type: %s", ct)
	}
	return ""
}

func (c *Context) parseQueryString(u *url.URL) string {
	if u == nil {
		return "missing request URL"
	}
	m, err := url.ParseQuery(u.RawQuery)
	if err != nil {
		return err.Error()
	}
	c.values = m
	return ""
}

func (c *Context) ParseFields() {
	if c.parent != nil {
		c.parent.ParseFields()
		return
	}
	if c.parsed {
		return
	}
	c.values = url.Values{}
	err := c.parseQueryString(c.request.URL)
	if err != "" {
		c.Errorf("web: couldn't parse query string: %s", err)
	}
	if c.request.Method == "POST" {
		err := c.parsePostBody(c.request)
		if err != "" {
			c.Errorf("web: couldn't parse POST body: %s", err)
		}
	}
	c.parsed = true
	return
}

func (c *Context) ParseSecureToken(name string, value string) string {
	return token.Parse(name, value, config.TokenKeys)
}

func (c *Context) Query(kind string) *model.Query {
	if txn := c.dataTxn(); txn != nil {
		return model.NewQuery(c, datastore.NewQuery(kind).Transaction(txn), 0)
	}
	return model.NewQuery(c, datastore.NewQuery(kind), config.QueryTimeout)
}

func (c *Context) RaiseNotFound() {
	panic(raise404{})
}

func (c *Context) RaiseRedirect(url string) {
	panic(raise301{url})
}

func (c *Context) Render(renderers ...Renderer) {
	if c.parent != nil {
		c.parent.Render(renderers...)
		return
	}
	content := c.buffer.Bytes()
	for _, renderer := range renderers {
		c.buffer = &bytes.Buffer{}
		renderer(c, content)
		content = c.buffer.Bytes()
	}
	c.buffer = &bytes.Buffer{}
	c.buffer.Write(content)
}

func (c *Context) RenderContent(content []byte, renderers ...Renderer) {
	if c.parent != nil {
		c.parent.RenderContent(content, renderers...)
		return
	}
	for _, renderer := range renderers {
		renderer(c, content)
		content = c.buffer.Bytes()
		c.buffer = &bytes.Buffer{}
	}
	c.buffer.Write(content)
}

func (c *Context) RenderPage(content []byte) {
	c.RenderContent(content, PageRenderers...)
}

func (c *Context) Request() *http.Request {
	if c.parent != nil {
		return c.parent.Request()
	}
	return c.request
}

func (c *Context) SecureToken(name string, value string) string {
	return token.New(name, value, config.TokenDuration, config.TokenSpec).String()
}

func (c *Context) SetBool(key string, value bool) {
	if c.parent != nil {
		c.parent.SetBool(key, value)
		return
	}
	if c.bools == nil {
		c.bools = map[string]bool{}
	}
	c.bools[key] = value
}

func (c *Context) SetCookie(name string, value string) {
	if c.parent != nil {
		c.parent.SetCookie(name, value)
		return
	}
	token := token.New("cookie/"+name, value, config.CookieDuration, config.TokenSpec)
	cookie := &http.Cookie{
		Name:     name,
		Value:    token.String(),
		HttpOnly: true,
		MaxAge:   config.CookieSeconds,
	}
	if !DevServer {
		cookie.Secure = true
	}
	c.cookies = append(c.cookies, cookie.String())
}

func (c *Context) SetInt(key string, value int64) {
	if c.parent != nil {
		c.parent.SetInt(key, value)
		return
	}
	if c.ints == nil {
		c.ints = map[string]int64{}
	}
	c.ints[key] = value
}

func (c *Context) SetPathArgs(args []string) {
	if c.parent != nil {
		c.parent.SetPathArgs(args)
		return
	}
	c.pathArgs = args
}

func (c *Context) SetResponseHeader(name string, value string) {
	if c.parent != nil {
		c.parent.SetResponseHeader(name, value)
		return
	}
	if c.headers == nil {
		c.headers = map[string]string{}
	}
	c.headers[name] = value
}

func (c *Context) SetResponseStatus(status int) {
	if c.parent != nil {
		c.parent.SetResponseStatus(status)
		return
	}
	c.status = status
}

func (c *Context) SetString(key string, value string) {
	if c.parent != nil {
		c.parent.SetString(key, value)
		return
	}
	if c.strings == nil {
		c.strings = map[string]string{}
	}
	c.strings[key] = value
}

func (c *Context) SetUser(user *model.User) {
	c.user = user
}

func (c *Context) SetUserID(id int64) {
	c.userID = id
}

func (c *Context) StringField(name string) string {
	if c.parent != nil {
		return c.parent.StringField(name)
	}
	c.ParseFields()
	return c.values.Get(name)
}

func (c *Context) StringSliceField(name string) []string {
	if c.parent != nil {
		return c.parent.StringSliceField(name)
	}
	c.ParseFields()
	if v, exists := c.values[name]; exists {
		return v
	}
	return nil
}

func (c *Context) Transact(f func(*Context) error) error {
	return c.TransactWithTimeout(config.TransactionTimeout, f)
}

func (c *Context) TransactWithTimeout(d time.Duration, f func(*Context) error) error {
	for n := 0; n < 3; n++ {
		ctx := c.WithTimeout(d)
		txn, err := config.DataClient.NewTransaction(ctx)
		if err != nil {
			ctx.Cancel()
			return err
		}
		ctx.txn = txn
		if err := f(ctx); err != nil {
			txn.Rollback()
			ctx.Cancel()
			return err
		}
		cmt, err := txn.Commit()
		ctx.Cancel()
		if err != nil {
			if err == datastore.ErrConcurrentTransaction {
				continue
			}
			return err
		}
		for _, key := range ctx.pending {
			key.Datastore = cmt.Key(key.Pending)
			key.Pending = nil
		}
		ctx.pending = nil
		return nil
	}
	return datastore.ErrConcurrentTransaction
}

func (c *Context) URL(elems ...string) string {
	if c.parent != nil {
		return c.parent.URL(elems...)
	}
	args := []string{}
	kwargs := url.Values{}
	key := ""
	for _, elem := range elems {
		if strings.HasSuffix(elem, "=") {
			key = elem[:len(elem)-1]
		} else if key != "" {
			kwargs.Set(key, elem)
			key = ""
		} else {
			args = append(args, elem)
		}
	}
	scheme := "https"
	host := c.request.Host
	if DevServer {
		scheme = "http"
	} else if config.CanonicalHost != "" {
		host = config.CanonicalHost
	}
	u := &url.URL{
		Scheme:   scheme,
		Host:     host,
		Path:     strings.Join(args, "/"),
		RawQuery: kwargs.Encode(),
	}
	return u.String()
}

func (c *Context) ValidateXSRF() bool {
	return c.ValidateXSRFValue(c.StringField("xsrf"))
}

func (c *Context) ValidateXSRFValue(token string) bool {
	return hmac.Equal([]byte(c.XSRF()), []byte(token))
}

func (c *Context) Value(key interface{}) interface{} {
	return nil
}

func (c *Context) WithTimeout(timeout time.Duration) *Context {
	deadline := time.Now().Add(timeout)
	if !c.deadline.IsZero() && c.deadline.Before(deadline) {
		return c
	}
	child := &Context{
		deadline: deadline,
		done:     make(chan struct{}),
		parent:   c,
	}
	c.mu.Lock()
	if c.err != nil {
		c.mu.Unlock()
		return c
	}
	if c.children == nil {
		c.children = map[*Context]struct{}{}
	}
	c.children[child] = struct{}{}
	c.mu.Unlock()
	child.mu.Lock()
	if child.err == nil {
		// Recalculate the timeout in case it took too long to acquire locks.
		timeout = deadline.Sub(time.Now())
		if timeout <= 0 {
			child.mu.Unlock()
			child.cancel(true, context.DeadlineExceeded)
			return child
		}
		child.timer = time.AfterFunc(timeout, func() {
			child.cancel(true, context.DeadlineExceeded)
		})
	}
	child.mu.Unlock()
	return child
}

func (c *Context) Write(p []byte) (int, error) {
	if c.parent != nil {
		return c.parent.Write(p)
	}
	return c.buffer.Write(p)
}

func (c *Context) WriteString(s string) (int, error) {
	if c.parent != nil {
		return c.parent.WriteString(s)
	}
	return c.buffer.Write([]byte(s))
}

func (c *Context) XSRF() string {
	if c.xsrf != "" {
		return c.xsrf
	}
	xsrf := c.GetCookie("xsrf")
	if xsrf != "" {
		c.xsrf = hex.EncodeToString([]byte(xsrf))
		return c.xsrf
	}
	buf := make([]byte, 36)
	_, err := rand.Read(buf)
	if err != nil {
		panic(err)
	}
	c.SetCookie("xsrf", string(buf))
	c.xsrf = hex.EncodeToString(buf)
	return c.xsrf
}

func newContext(r *http.Request, timeout time.Duration) *Context {
	c := &Context{
		buffer:  &bytes.Buffer{},
		request: r,
		status:  200,
	}
	if timeout > 0 {
		c.deadline = time.Now().Add(timeout)
		c.done = make(chan struct{})
		c.timer = time.AfterFunc(timeout, func() {
			c.cancel(false, context.DeadlineExceeded)
		})
	}
	return c
}

func BackgroundContext() *Context {
	req := &http.Request{
		Host: ServerHost,
	}
	return newContext(req, 0)
}
