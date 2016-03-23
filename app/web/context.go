// Public Domain (-) 2016 The GitFund Authors.
// See the GitFund UNLICENSE file for details.

package web

import (
	"bytes"
	"net/http"

	"github.com/tav/gitfund/app/model"
	"github.com/tav/gitfund/app/page"
	"golang.org/x/net/context"
	"google.golang.org/appengine"
	"google.golang.org/appengine/log"
)

var (
	DevServer    = false
	PageTemplate Renderer
	SiteTemplate Renderer
)

type Context struct {
	AppEngine context.Context
	Args      []string
	Buffer    *bytes.Buffer
	Data      map[string]string
	Options   map[string]bool
	Request   *http.Request
	Response  http.ResponseWriter
	useBuf    bool
	user      *model.User
	userID    int64
	xsrf      string
	written   bool
}

type Renderer func(c *Context, content []byte)

func (c *Context) Errorf(format string, args ...interface{}) {
	log.Errorf(c.AppEngine, format, args...)
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

func (c *Context) Redirect(url string) {
	if c.written {
		c.Errorf("web: Redirect called despite response having been written")
		return
	}
	http.Redirect(c.Response, c.Request, url, http.StatusMovedPermanently)
	c.written = true
}

func (c *Context) Render(content []byte, renderers ...Renderer) {
	if len(renderers) == 1 {
		renderers[0](c, content)
	} else if len(renderers) == 0 {
		c.Response.Write(content)
		c.written = true
	} else {
		c.UseBuffer(true)
		for _, tmpl := range renderers {
			c.Buffer.Reset()
			tmpl(c, content)
			content = c.Buffer.Bytes()
		}
		c.UseBuffer(false)
		c.Response.Write(content)
		c.written = true
	}
}

func (c *Context) RenderPage(content []byte) {
	c.Render(content, PageTemplate, SiteTemplate)
}

func (c *Context) Serve404() {
	if c.written {
		c.Errorf("web: Serve404 called despite response having been written")
		return
	}
	c.Data["title"] = "Page Not Found"
	c.Response.WriteHeader(404)
	c.Response.Header().Set("Content-Type", "text/html; charset=utf-8")
	c.RenderPage(page.ERROR_404)
}

func (c *Context) Serve500() {
	if c.written {
		c.Errorf("web: Serve500 called despite response having been written")
		return
	}
	c.Data["title"] = "Service Unavailable"
	c.Response.WriteHeader(500)
	c.Response.Header().Set("Content-Type", "text/html; charset=utf-8")
	c.RenderPage(page.ERROR_500)
}

func (c *Context) UseBuffer(state bool) {
	c.useBuf = state
}

func (c *Context) User() *model.User {
	userID := c.UserID()
	if userID == 0 {
		return nil
	}
	return nil
}

func (c *Context) UserID() int64 {
	return 0
}

func (c *Context) ValidateXSRF(token string) bool {
	return false
}

func (c *Context) Write(p []byte) (int, error) {
	if c.useBuf {
		return c.Buffer.Write(p)
	}
	c.written = true
	return c.Response.Write(p)
}

func (c *Context) XSRF() string {
	return ""
}

func NewContext(w http.ResponseWriter, r *http.Request) *Context {
	return &Context{
		AppEngine: appengine.NewContext(r),
		Args:      []string{},
		Buffer:    &bytes.Buffer{},
		Data:      map[string]string{},
		Options:   map[string]bool{},
		Request:   r,
		Response:  w,
	}
}

func init() {
	DevServer = appengine.IsDevAppServer()
}
