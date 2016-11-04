// Public Domain (-) 2016 The GitFund Authors.
// See the GitFund UNLICENSE file for details.

package main

import (
	"errors"
	"fmt"
	"io/ioutil"
	"net/url"
	"os"
	"strings"
	"time"

	"github.com/google/go-github/github"
	"github.com/tav/golly/optparse"
	"github.com/tav/slack"
	"golang.org/x/oauth2"
	"gopkg.in/yaml.v2"
)

const (
	maxUpdates  = 5
	maxDuration = time.Hour
)

var (
	config   = &Config{}
	ghClient = &github.Client{}
	posts    = make(chan *Post, 10000)
)

type Config struct {
	Channels map[string][]string
	GitHub   struct {
		Token string `yaml:"access_token"`
		URL   string `yaml:"api_url_base"`
	}
	Slack struct {
		API string `yaml:"api_token"`
	}
}

type Post struct {
	Channel string
	Message string
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
	if commit.Committer != nil && *commit.Committer.Login != "" {
		return *commit.Committer.Login
	}
	if commit.Commit.Author != nil && *commit.Commit.Author.Name != "" {
		return *commit.Commit.Author.Name
	}
	if commit.Commit.Committer != nil && *commit.Commit.Committer.Name != "" {
		return *commit.Commit.Committer.Name
	}
	return "-"
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

func slackBot() {

	client := slack.New(config.Slack.API)
	ids := map[string]string{}

	channels, err := client.GetChannels(true)
	if err != nil {
		exit(err)
	}

	for _, channel := range channels {
		ids[channel.Name] = channel.ID
	}

	groups, err := client.GetGroups(true)
	if err != nil {
		exit(err)
	}

	for _, group := range groups {
		ids[group.Name] = group.ID
	}

	statusMap := map[string]*Status{}
	for channel, repos := range config.Channels {
		chanID, exists := ids[channel]
		if !exists {
			exit(fmt.Errorf(
				"Cannot find channel %q: perhaps it's a typo or the bot hasn't been invited to the channel?",
				channel))
		}
		statusMap[chanID] = &Status{}
		for _, path := range repos {
			go watchRepo(chanID, path)
		}
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
		case post := <-posts:
			status := statusMap[post.Channel]
			if status.UpdatePrev && time.Now().UTC().Sub(status.UpdateTime) < maxDuration {
				status.Message += "\n" + post.Message
				_, _, _, err = client.UpdateMessage(post.Channel, status.ID, status.Message)
				if err != nil {
					fmt.Printf("ERROR: %s\n", err)
					break
				}
				status.UpdateCount += 1
			} else {
				status.Message = post.Message
				_, postID, err := client.PostMessage(post.Channel, status.Message, msgParams)
				if err != nil {
					fmt.Printf("ERROR: %s\n", err)
					break
				}
				status.ID = postID
				status.UpdateCount = 1
				status.UpdateTime = time.Now().UTC()
			}
			if status.UpdateCount == maxUpdates {
				status.UpdateCount = 0
				status.UpdatePrev = false
			} else {
				status.UpdatePrev = true
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
				fmt.Printf("ERROR: %s\n", e.Error())
			}
		}
	}

}

func stripHash(channel string) string {
	if strings.HasPrefix(channel, "#") {
		return channel[1:]
	}
	return channel
}

func watchRepo(channel string, path string) {
	split := strings.Split(path, "/")
	if len(split) != 2 {
		exit(fmt.Errorf("Invalid repo path: %q", path))
	}
	owner, repo := split[0], split[1]
	opts := &github.CommitsListOptions{ListOptions: github.ListOptions{PerPage: 50}}
	seen := ""
	for {
		commits, _, err := ghClient.Repositories.ListCommits(owner, repo, opts)
		if err != nil {
			fmt.Printf("ERROR: Couldn't fetch commits from %q: %s", path, err)
			time.Sleep(30 * time.Second)
			continue
		}
		latest := ""
		msgs := []string{}
		for _, commit := range commits {
			if latest == "" {
				latest = *commit.SHA
			}
			if seen == "" || *commit.SHA == seen {
				break
			}
			msgs = append(msgs, fmt.Sprintf(
				"➜  %s  `<%s|%s>`",
				getCommitMessage(commit),
				*commit.HTMLURL,
				repo,
			))
		}
		seen = latest
		if len(msgs) > 0 {
			for i := len(msgs) - 1; i >= 0; i-- {
				posts <- &Post{
					Channel: channel,
					Message: msgs[i],
				}
			}
		}
		time.Sleep(15 * time.Second)
	}
}

func main() {

	opts := optparse.New("Usage: github-slack path/to/config.yaml")
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

	ghClient = github.NewClient(oauth2.NewClient(
		oauth2.NoContext,
		oauth2.StaticTokenSource(&oauth2.Token{AccessToken: config.GitHub.Token}),
	))

	if config.GitHub.URL != "" && config.GitHub.URL != "https://api.github.com/" {
		baseURL, err := url.Parse(config.GitHub.URL)
		if err != nil {
			exit(err)
		}
		ghClient.BaseURL = baseURL
	}

	nchannels := map[string][]string{}
	for channel, repos := range config.Channels {
		nchannels[stripHash(channel)] = repos
	}

	config.Channels = nchannels

	go slackBot()

	<-make(chan struct{})

}
