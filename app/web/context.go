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
	"time"

	"github.com/tav/gitfund/app/config"
	"github.com/tav/gitfund/app/token"
	"github.com/tav/golly/log"
	"google.golang.org/appengine"
)

var cookieExpire, _ = time.Parse(http.TimeFormat, "Fri, 31 Dec 99 23:59:59 GMT")

type Context struct {
	context.Context
	Args     []string
	Bools    map[string]bool
	Request  *http.Request
	Strings  map[string]string
	buffer   *bytes.Buffer
	cookies  []string
	files    map[string][]*multipart.FileHeader
	headers  map[string]string
	output   []byte
	parsed   bool
	response http.ResponseWriter
	status   int
	user     interface{}
	userID   int64
	xsrf     string
	values   url.Values
	written  bool
}

func (c *Context) ClearHeaders() {
	c.cookies = []string{}
	c.headers = map[string]string{}
}

func (c *Context) Debugf(format string, args ...interface{}) {
	log.Debugf(format, args...)
}

func (c *Context) DirectOutput(o []byte) {
	c.output = o
	c.written = true
}

func (c *Context) EncodeJSON(v interface{}) {
	c.headers["Content-Type"] = "application/json"
	enc := json.NewEncoder(c.buffer)
	err := enc.Encode(v)
	if err != nil {
		panic(err)
	}
}

func (c *Context) Errorf(format string, args ...interface{}) {
	log.Errorf(format, args...)
}

func (c *Context) ExpireCookie(name string) {
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

func (c *Context) DecodeJSON(v interface{}) error {
	ct, _, _ := mime.ParseMediaType(c.Request.Header.Get("Content-Type"))
	if ct != "application/json" {
		return fmt.Errorf("web: unsupported content type for decoding JSON: %s", ct)
	}
	return json.NewDecoder(c.Request.Body).Decode(v)
}

func (c *Context) GetBool(name string) bool {
	c.Parse()
	if c.values.Get(name) == "" {
		return false
	}
	return true
}

func (c *Context) GetCookie(name string) string {
	cookie, err := c.Request.Cookie(name)
	if err != nil {
		return ""
	}
	return c.ParseToken("cookie/"+name, cookie.Value)
}

func (c *Context) GetFile(name string) (multipart.File, *multipart.FileHeader, error) {
	c.Parse()
	if c.files != nil {
		if files := c.files[name]; len(files) > 0 {
			f, err := files[0].Open()
			return f, files[0], err
		}
	}
	return nil, nil, http.ErrMissingFile
}

func (c *Context) GetInt(name string) int64 {
	c.Parse()
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

func (c *Context) GetString(name string) string {
	c.Parse()
	return c.values.Get(name)
}

func (c *Context) GetStringSlice(name string) []string {
	c.Parse()
	if v, exists := c.values[name]; exists {
		return v
	}
	return []string{}
}

func (c *Context) Infof(format string, args ...interface{}) {
	log.Infof(format, args...)
}

func (c *Context) IsCronRequest() bool {
	return c.Request.Header.Get("X-AppEngine-Cron") != "" || DevServer
}

func (c *Context) IsTaskRequest() bool {
	return c.Request.Header.Get("X-AppEngine-TaskName") != "" || DevServer
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
	default:
		return fmt.Sprintf("unsupported POST content-type: %s", ct)
	}
	return ""
}

func (c *Context) Parse() {
	if c.parsed {
		return
	}
	c.values = url.Values{}
	err := c.parseQueryString(c.Request.URL)
	if err != "" {
		c.Errorf("web: couldn't parse query string: %s", err)
	}
	if c.Request.Method == "POST" {
		err := c.parsePostBody(c.Request)
		if err != "" {
			c.Errorf("web: couldn't parse POST body: %s", err)
		}
	}
	c.parsed = true
	return
}

func (c *Context) ParseToken(name string, value string) string {
	return token.Parse(name, value, config.TokenKeys)
}

func (c *Context) RaiseNotFound() {
	panic(raise404{})
}

func (c *Context) RaiseRedirect(url string) {
	panic(raise301{url})
}

func (c *Context) Render(renderers ...Renderer) {
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

func (c *Context) SetCookie(name string, value string) {
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

func (c *Context) SetHeader(name string, value string) {
	c.headers[name] = value
}

func (c *Context) SetStatus(status int) {
	c.status = status
}

func (c *Context) Token(name string, value string) string {
	return token.New(name, value, config.TokenDuration, config.TokenSpec).String()
}

func (c *Context) ValidateXSRF() bool {
	return c.ValidateXSRFValue(c.GetString("xsrf"))
}

func (c *Context) ValidateXSRFValue(token string) bool {
	return hmac.Equal([]byte(c.XSRF()), []byte(token))
}

func (c *Context) Write(p []byte) (int, error) {
	return c.buffer.Write(p)
}

func (c *Context) WriteString(s string) (int, error) {
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

func (c *Context) URL(elems ...string) string {
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
	if DevServer {
		scheme = "http"
	}
	host := config.CanonicalHost
	if host != "" {
		host = c.Request.Host
	}
	u := &url.URL{
		Scheme:   scheme,
		Host:     host,
		Path:     strings.Join(args, "/"),
		RawQuery: kwargs.Encode(),
	}
	return u.String()
}

func NewContext(w http.ResponseWriter, r *http.Request) *Context {
	return &Context{
		Context:  appengine.NewContext(r),
		Args:     []string{},
		Bools:    map[string]bool{},
		Request:  r,
		Strings:  map[string]string{},
		buffer:   &bytes.Buffer{},
		cookies:  []string{},
		headers:  map[string]string{},
		response: w,
		status:   200,
	}
}
