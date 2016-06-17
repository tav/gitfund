// Public Domain (-) 2016 The GitFund Authors.
// See the GitFund UNLICENSE file for details.

package web

import (
	"bytes"
	"crypto/hmac"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"mime"
	"net/http"
	"net/url"
	"strconv"
	"strings"
	"time"

	"golang.org/x/net/context"
	"google.golang.org/appengine"
	"google.golang.org/appengine/log"
)

var cookieExpire, _ = time.Parse(http.TimeFormat, "Fri, 31 Dec 99 23:59:59 GMT")

type Context struct {
	AppEngine context.Context
	Args      []string
	Data      map[string]string
	Options   map[string]bool
	Request   *http.Request
	buffer    *bytes.Buffer
	cookies   []string
	headers   map[string]string
	output    []byte
	parsed    bool
	response  http.ResponseWriter
	status    int
	user      interface{}
	userID    int64
	xsrf      string
	values    url.Values
	written   bool
}

func (c *Context) ClearHeaders() {
	c.headers = map[string]string{}
}

func (c *Context) DirectOutput(o []byte) {
	c.output = o
	c.written = true
}

func (c *Context) EncodeJSON(v interface{}) {
	enc := json.NewEncoder(c.buffer)
	err := enc.Encode(v)
	if err != nil {
		panic(err)
	}
}

func (c *Context) Errorf(format string, args ...interface{}) {
	log.Errorf(c.AppEngine, format, args...)
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

func (c *Context) parse() {
	if c.parsed {
		return
	}
	c.values = url.Values{}
}

func (c *Context) GetBool(attr string) bool {
	c.parse()
	if c.values.Get(attr) == "" {
		return false
	}
	return true
}

func (c *Context) GetCookie(name string) string {
	cookie, err := c.Request.Cookie(name)
	if err != nil {
		return ""
	}
	return ParseToken("cookie/"+name, cookie.Value)
}

func (c *Context) GetInt(attr string) int64 {
	c.parse()
	val := c.values.Get(attr)
	if val == "" {
		return 0
	}
	v, err := strconv.ParseInt(val, 10, 64)
	if err != nil {
		return 0
	}
	return v
}

func (c *Context) GetFile(attr string) bool {
	return false
}

func (c *Context) GetString(attr string) string {
	c.parse()
	return c.values.Get(attr)
}

func (c *Context) GetStringSlice(attr string) []string {
	c.parse()
	if v, exists := c.values[attr+"[]"]; exists {
		return v
	}
	return []string{}
}

func (c *Context) Infof(format string, args ...interface{}) {
	log.Infof(c.AppEngine, format, args...)
}

func (c *Context) IsCronRequest() bool {
	return c.Request.Header.Get("X-AppEngine-Cron") != "" || DevServer
}

func (c *Context) IsTaskRequest() bool {
	return c.Request.Header.Get("X-AppEngine-TaskName") != "" || DevServer
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
	c.RenderContent(content, pageRenderers...)
}

func (c *Context) SendEmail(from string, to string, body []string) {
}

func (c *Context) SetCookie(name string, value string) {
	token := NewToken("cookie/"+name, value, cookieDuration)
	cookie := &http.Cookie{
		Name:     name,
		Value:    token.String(),
		HttpOnly: true,
		MaxAge:   cookieSeconds,
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
	host := canonicalHost
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
	r.Body = http.MaxBytesReader(w, r.Body, 32<<20) // 32MB
	return &Context{
		AppEngine: appengine.NewContext(r),
		Args:      []string{},
		Data:      map[string]string{},
		Options:   map[string]bool{},
		Request:   r,
		buffer:    &bytes.Buffer{},
		cookies:   []string{},
		headers:   map[string]string{},
		response:  w,
		status:    200,
	}
}
