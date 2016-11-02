// Public Domain (-) 2016 The GitFund Authors.
// See the GitFund UNLICENSE file for details.

package main

import (
	"time"

	"github.com/tav/gitfund/app/config"
	"github.com/tav/gitfund/app/template"
	"github.com/tav/gitfund/app/web"
	"github.com/tav/gitfund/app/worker"
)

func lookup(c *web.Context) (*web.Route, bool) {
	return nil, false
}

func main() {
	web.Register(&web.Dispatcher{
		Path:   "/",
		Lookup: lookup,
		Queues: []*config.Queue{config.Queue1, config.Queue10},
		Routes: web.Routes{
			"/": {
				Anon:    true,
				Handler: handleRoot,
			},
			"env": {
				Anon:    true,
				Handler: handleEnviron,
			},
			"home": {
				Anon:    true,
				Handler: handleHome,
			},
			"site": {
				Anon:      true,
				Handler:   handleSite,
				Renderers: []web.Renderer{template.Page},
			},
		},
		Statics: map[string]*web.Static{
			"_assets":     {Directory: "_assets", Expiration: 14 * 24 * time.Hour},
			"favicon.ico": {File: "favicon.ico", Expiration: 24 * time.Hour},
			"humans.txt":  {File: "humans.txt", Expiration: 24 * time.Hour},
			"robots.txt":  {File: "robots.txt", Expiration: 24 * time.Hour},
		},
		Workers: worker.Config,
	})
	web.PageRenderers = []web.Renderer{template.Page, template.Main}
	web.Run()
}
