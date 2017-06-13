// Public Domain (-) 2016-2017 The GitFund Authors.
// See the GitFund UNLICENSE file for details.

package main

import (
	"crypto/tls"
	"errors"
	"fmt"
	"io/ioutil"
	"net/http"
	"net/url"
	"os"
	"strings"
	"time"

	"github.com/google/go-github/github"
	"github.com/tav/golly/optparse"
	"github.com/tav/golly/process"
	"github.com/tav/slack"
	"github.com/thoj/go-ircevent"
	"golang.org/x/oauth2"
	"gopkg.in/yaml.v2"
)

var (
	config      = &Config{}
	ircEvents   = make(chan *Event, 10000)
	slackEvents = make(chan *Event, 10000)
)

type ChanSpec struct {
	IRC   []string
	Slack []string
}

type Commit struct {
	By       string
	Message  string
	Path     string
	Repo     string
	ShortURL string
	URL      string
}

type Config struct {
	GitHub struct {
		Token string `yaml:"access_token"`
		URL   string `yaml:"api_url_base"`
	}
	IRC struct {
		Auth struct {
			Type     string
			Password string
		}
		Channels map[string][]string
		Nick     string
		Port     int
		QuitMsg  string
		Server   string
		TLS      bool
	}
	Slack struct {
		API         string        `yaml:"api_token"`
		MaxDuration time.Duration `yaml:"max_duration"`
		MaxLines    int           `yaml:"max_lines"`
		Channels    map[string][]string
	}
}

type Event struct {
	Channels []string
	Commit   *Commit
}

type Status struct {
	ID          string
	Message     string
	UpdateCount int
	UpdatePrev  bool
	UpdateTime  time.Time
}

func exit(err error) {
	fmt.Printf("ERROR: %s\n", err)
	os.Exit(1)
}

func getAuthor(commit *github.RepositoryCommit) string {
	if commit.Author != nil && *commit.Author.Login != "" {
		return *commit.Author.Login
	}
	if commit.Commit.Author != nil && *commit.Commit.Author.Name != "" {
		return *commit.Commit.Author.Name
	}
	if commit.Committer != nil && *commit.Committer.Login != "" {
		return *commit.Committer.Login
	}
	if commit.Commit.Committer != nil && *commit.Commit.Committer.Name != "" {
		return *commit.Commit.Committer.Name
	}
	return ""
}

func getCommitMessage(commit *github.RepositoryCommit) string {
	msg := strings.TrimSpace(strings.Split(*commit.Commit.Message, "\n")[0])
	if strings.HasSuffix(msg, ".") {
		return msg[:len(msg)-1]
	}
	return msg
}

func getRepoURL(commit *github.RepositoryCommit) string {
	splitURL := strings.Split(*commit.HTMLURL, "/commit/")
	return strings.Join(splitURL[:len(splitURL)-1], "/commit/")
}

func ircBot() {

	stage1 := make(chan struct{})
	stage2 := make(chan struct{})

	conn := irc.IRC(config.IRC.Nick, config.IRC.Nick)
	conn.QuitMessage = config.IRC.QuitMsg
	if config.IRC.TLS {
		conn.TLSConfig = &tls.Config{ServerName: config.IRC.Server}
		conn.UseTLS = true
	}

	conn.AddCallback("001", func(e *irc.Event) {
		go func() {
			<-stage1
			for channel := range config.IRC.Channels {
				conn.Join(channel)
			}
			stage2 <- struct{}{}
		}()
		if config.IRC.Auth.Type == "nickserv" {
			conn.Privmsgf("nickserv", "identify %s %s", config.IRC.Nick, config.IRC.Auth.Password)
			if conn.GetNick() != config.IRC.Nick {
				conn.AddCallback("NOTICE", func(ev *irc.Event) {
					if strings.ToLower(ev.Nick) != "nickserv" {
						return
					}
					if !strings.Contains(ev.Arguments[1], "has been ghosted") {
						return
					}
					conn.Nick(config.IRC.Nick)
					stage1 <- struct{}{}
				})
				conn.Privmsgf("nickserv", "ghost %s %s", config.IRC.Nick, config.IRC.Auth.Password)
			} else {
				stage1 <- struct{}{}
			}
		} else {
			stage1 <- struct{}{}
		}
	})

	err := conn.Connect(fmt.Sprintf("%s:%d", config.IRC.Server, config.IRC.Port))
	if err != nil {
		exit(err)
	}

	process.SetExitHandler(func() {
		fmt.Println("Quiting IRC ...")
		conn.Quit()
	})

	<-stage2
	for event := range ircEvents {
		commit := event.Commit
		msg := commit.Message
		if len(msg) > 350 {
			msg = msg[:350]
			if msg[349] == ' ' {
				msg += "... [truncated]"
			} else {
				msg += " ... [truncated]"
			}
		}
		msg = fmt.Sprintf("➜ %s %s  [%s]", msg, commit.ShortURL, commit.Repo)
		if commit.By != "" {
			msg += " — " + commit.By
		}
		for _, channel := range event.Channels {
			conn.Privmsg(channel, msg)
		}
	}

}

func shortenURL(link string) string {
	resp, err := http.PostForm("https://git.io", url.Values{
		"url": []string{link},
	})
	if err != nil {
		fmt.Printf("ERROR: Unable to shorten URL using git.io: %s\n", err)
		return ""
	}
	resp.Body.Close()
	loc, err := resp.Location()
	if err != nil {
		fmt.Printf("ERROR: No location found in the response from git.io: %s\n", err)
		return ""
	}
	return loc.String()
}

func slackBot() {

	client := slack.New(config.Slack.API)
	ids := map[string]string{}

	channels, err := client.GetChannels(true)
	if err != nil {
		exit(err)
	}

	for _, channel := range channels {
		ids["#"+strings.ToLower(channel.Name)] = channel.ID
	}

	groups, err := client.GetGroups(true)
	if err != nil {
		exit(err)
	}

	for _, group := range groups {
		ids[strings.ToLower(group.Name)] = group.ID
	}

	statusMap := map[string]*Status{}
	for channel := range config.Slack.Channels {
		chanID, exists := ids[strings.ToLower(channel)]
		if !exists {
			exit(fmt.Errorf(
				"Cannot find channel %s: perhaps it's a typo or the bot hasn't been invited to the channel?",
				channel))
		}
		statusMap[chanID] = &Status{}
	}

	self, err := client.AuthTest()
	if err != nil {
		exit(err)
	}

	selfID := self.UserID
	rtm := client.NewRTM()
	go rtm.ManageConnection()

	msgParams := slack.PostMessageParameters{
		AsUser:      true,
		Markdown:    false,
		UnfurlLinks: false,
	}

	for {
		select {
		case event := <-slackEvents:
			commit := event.Commit
			msg := fmt.Sprintf(
				"➜  %s  `<%s|%s>`",
				commit.Message,
				commit.URL,
				commit.Repo,
			)
			if commit.By != "" {
				msg += " — " + commit.By
			}
			for _, channel := range event.Channels {
				chanID := ids[channel]
				status := statusMap[chanID]
				if status.UpdatePrev && time.Now().UTC().Sub(status.UpdateTime) < config.Slack.MaxDuration {
					status.Message += "\n" + msg
					_, _, _, err = client.UpdateMessage(chanID, status.ID, status.Message)
					if err != nil {
						fmt.Printf("ERROR: %s\n", err)
						break
					}
					status.UpdateCount += 1
				} else {
					status.Message = msg
					_, postID, err := client.PostMessage(chanID, status.Message, msgParams)
					if err != nil {
						fmt.Printf("ERROR: %s\n", err)
						break
					}
					status.ID = postID
					status.UpdateCount = 1
					status.UpdateTime = time.Now().UTC()
				}
				if status.UpdateCount >= config.Slack.MaxLines {
					status.UpdateCount = 0
					status.UpdatePrev = false
				} else {
					status.UpdatePrev = true
				}
			}
		case msg := <-rtm.IncomingEvents:
			switch e := msg.Data.(type) {
			case *slack.MessageEvent:
				if e.Hidden || e.User == selfID {
					break
				}
				if status, exists := statusMap[e.Channel]; exists && status.UpdatePrev {
					status.UpdateCount = 0
					status.UpdatePrev = false
				}
			case *slack.InvalidAuthEvent:
				exit(errors.New("slack: invalid auth credentials"))
			case *slack.RTMError:
				fmt.Printf("ERROR: %s\n", e)
			}
		}
	}

}

func watchRepo(client *github.Client, path string, spec *ChanSpec) {
	split := strings.Split(path, "/")
	if len(split) != 2 {
		exit(fmt.Errorf("Invalid repo path: %q", path))
	}
	updateIRC := len(spec.IRC) > 0
	updateSlack := len(spec.Slack) > 0
	owner, repo := split[0], split[1]
	opts := &github.CommitsListOptions{ListOptions: github.ListOptions{PerPage: 50}}
	seen := ""
	for {
		commits, _, err := client.Repositories.ListCommits(owner, repo, opts)
		if err != nil {
			fmt.Printf("ERROR: Couldn't fetch commits from %q: %s\n", path, err)
			time.Sleep(30 * time.Second)
			continue
		}
		latest := ""
		pending := []*Commit{}
		for _, commit := range commits {
			if latest == "" {
				latest = *commit.SHA
			}
			if seen == "" || *commit.SHA == seen {
				break
			}
			pending = append(pending, &Commit{
				By:       getAuthor(commit),
				Message:  getCommitMessage(commit),
				Path:     path,
				Repo:     repo,
				ShortURL: shortenURL(*commit.HTMLURL),
				URL:      *commit.HTMLURL,
			})
		}
		seen = latest
		if len(pending) > 0 {
			for i := len(pending) - 1; i >= 0; i-- {
				commit := pending[i]
				if updateIRC {
					ircEvents <- &Event{
						Channels: spec.IRC,
						Commit:   commit,
					}
				}
				if updateSlack {
					slackEvents <- &Event{
						Channels: spec.Slack,
						Commit:   commit,
					}
				}
			}
		}
		time.Sleep(15 * time.Second)
	}
}

func watchRepos() {
	client := github.NewClient(oauth2.NewClient(
		oauth2.NoContext,
		oauth2.StaticTokenSource(&oauth2.Token{AccessToken: config.GitHub.Token}),
	))
	if config.GitHub.URL != "" && config.GitHub.URL != "https://api.github.com/" {
		baseURL, err := url.Parse(config.GitHub.URL)
		if err != nil {
			exit(err)
		}
		client.BaseURL = baseURL
	}
	repo2spec := map[string]*ChanSpec{}
	for channel, repos := range config.Slack.Channels {
		channel = strings.ToLower(channel)
		for _, repo := range repos {
			repo = strings.ToLower(repo)
			spec, exists := repo2spec[repo]
			if !exists {
				spec = &ChanSpec{}
				repo2spec[repo] = spec
			}
			spec.Slack = append(spec.Slack, channel)
		}
	}
	for channel, repos := range config.IRC.Channels {
		channel = strings.ToLower(channel)
		for _, repo := range repos {
			repo = strings.ToLower(repo)
			spec, exists := repo2spec[repo]
			if !exists {
				spec = &ChanSpec{}
				repo2spec[repo] = spec
			}
			spec.IRC = append(spec.IRC, channel)
		}
	}
	for repo, spec := range repo2spec {
		go watchRepo(client, repo, spec)
	}
}

func main() {

	opts := optparse.New("Usage: github-bot path/to/config.yaml")
	args := opts.Parse(os.Args)
	if len(args) != 1 {
		opts.PrintUsage()
		os.Exit(1)
	}

	cdata, err := ioutil.ReadFile(args[0])
	if err != nil {
		exit(err)
	}

	err = yaml.Unmarshal(cdata, config)
	if err != nil {
		exit(err)
	}

	go ircBot()
	go slackBot()
	go watchRepos()

	<-make(chan struct{})

}
