// Public Domain (-) 2016 The GitFund Authors.
// See the GitFund UNLICENSE file for details.

package web

import (
	"strconv"

	"github.com/tav/gitfund/app/model"
	"github.com/tav/gitfund/app/page"
	"github.com/tav/golly/httputil"
)

var (
	htmlHeader = map[string]string{"Content-Type": "text/html; charset=utf-8"}
	jsonHeader = map[string]string{"Content-Type": "application/json"}
)

var (
	json404 = []byte(`{"error": "web: 404 page not found"}`)
	json500 = []byte(`{"error": "web: 500 service unavailable"}`)
)

func serveJSON(c *Context) bool {
	prefs := httputil.Parse(c.request, "Accept").FindPreferred("text/html", "application/json")
	if len(prefs) > 0 && prefs[0] == "application/json" {
		return true
	}
	return false
}

func (c *Context) serve404() {
	c.cookies = nil
	c.status = 404
	if serveJSON(c) {
		c.headers = jsonHeader
		c.DirectOutput(json404)
		return
	}
	c.headers = htmlHeader
	c.SetString("title", "Page Not Found")
	c.RenderPage(page.ERROR_404)
}

func (c *Context) serve500() {
	c.cookies = nil
	c.status = 500
	if serveJSON(c) {
		c.headers = jsonHeader
		c.DirectOutput(json500)
		return
	}
	c.headers = htmlHeader
	c.SetString("title", "Service Unavailable")
	c.RenderPage(page.ERROR_500)
}

func (c *Context) IsAdmin() bool {
	if c.parent != nil {
		return c.parent.IsAdmin()
	}
	userID := c.UserID()
	if userID == 0 {
		return false
	}
	return false
}

func (c *Context) LoginURL(redirect ...string) string {
	if c.parent != nil {
		return c.parent.LoginURL(redirect...)
	}
	return ""
}

func (c *Context) SendEmail(from string, to string, body []string) {
}

func (c *Context) User() *model.User {
	if c.parent != nil {
		return c.parent.User()
	}
	if c.user != nil {
		return c.user
	}
	userID := c.UserID()
	if userID == 0 {
		return nil
	}
	user, err := c.UserByID(userID)
	if err != nil {
		c.Errorf("web: couldn't get user %d: %s", userID, err)
		return nil
	}
	c.user = user
	return user
}

func (c *Context) UserID() int64 {
	if c.parent != nil {
		return c.parent.UserID()
	}
	if c.userID > 0 {
		return c.userID
	}
	if c.userID < 0 {
		return 0
	}
	auth := c.GetCookie("auth")
	if auth == "" {
		c.userID = -1
		return 0
	}
	userID, err := strconv.ParseInt(auth, 10, 64)
	if err != nil {
		c.Errorf("web: couldn't get userID from auth value %q: %s", auth, err)
		c.userID = -1
		return 0
	}
	c.userID = userID
	return userID
}
