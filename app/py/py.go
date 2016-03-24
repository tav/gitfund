// Public Domain (-) 2015-2016 The GitFund Authors.
// See the GitFund UNLICENSE file for details.

package py

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/tav/gitfund/app/config"
	"github.com/tav/gitfund/app/template"
	"golang.org/x/net/context"
	"google.golang.org/appengine"
	"google.golang.org/appengine/log"
	"google.golang.org/appengine/urlfetch"
)

var (
	baseURL = "http://localhost:8080/.python/"
	token   = []byte(config.PythonToken)
)

type callResponse struct {
	Error  string          `json:"error"`
	Result json.RawMessage `json:"result"`
}

type hiliteRequest struct {
	Code string `json:"code"`
	Lang string `json:"lang"`
}

func logError(c context.Context, format string, args ...interface{}) error {
	err := fmt.Errorf(format, args...)
	log.Errorf(c, "%s", err)
	return err
}

func Call(c context.Context, service string, request interface{}, response interface{}) error {
	client := &http.Client{Transport: &urlfetch.Transport{
		Context:  c,
		Deadline: 40 * time.Second,
	}}
	body := &bytes.Buffer{}
	body.Write(token)
	enc := json.NewEncoder(body)
	err := enc.Encode(request)
	if err != nil {
		return logError(c, "%s: couldn't encode the request into JSON: %s", service, err)
	}
	resp, err := client.Post(baseURL+service, "", body)
	if err != nil {
		return logError(c, "%s: got an HTTP client error: %s", service, err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		return logError(c, "%s: got HTTP status code: %d", service, resp.StatusCode)
	}
	dec := json.NewDecoder(resp.Body)
	jsonResp := &callResponse{}
	err = dec.Decode(jsonResp)
	if err != nil {
		return logError(c, "%s: couldn't decode the JSON response: %s", service, err)
	}
	if jsonResp.Error != "" {
		return logError(c, "%s: %s", service, jsonResp.Error)
	}
	err = json.Unmarshal(jsonResp.Result, response)
	if err != nil {
		return logError(c, "%s: couldn't decode the JSON result value: %s", service, err)
	}
	return nil
}

func Hilite(c context.Context, code string, lang string) string {
	var resp string
	err := Call(c, "hilite", &hiliteRequest{Code: code, Lang: lang}, &resp)
	if err != nil {
		return `<div class="syntax"><pre>` + template.EscapeString(code) + `</pre></div>`
	}
	return resp
}

func init() {
	if !appengine.IsDevAppServer() {
		baseURL = "https://" + config.AppID + ".appspot.com/.python/"
	}
}
