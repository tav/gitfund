// Public Domain (-) 2016 The GitFund Authors.
// See the GitFund UNLICENSE file for details.

package main

import (
	"crypto/tls"
	"errors"
	"fmt"
	"io/ioutil"
	"os"
	"strings"

	"github.com/nlopes/slack"
	"github.com/tav/golly/optparse"
	"github.com/tav/golly/process"
	"github.com/thoj/go-ircevent"
	"gopkg.in/yaml.v2"
)

var (
	config    = &Config{}
	ircMsgs   = make(chan string, 10000)
	slackMsgs = make(chan string, 10000)
)

type Config struct {
	IRC struct {
		Auth struct {
			Type     string
			Password string
		}
		Channel string
		Nick    string
		Port    int
		Privacy bool
		QuitMsg string
		Server  string
		TLS     bool
	}
	Slack struct {
		API     string `yaml:"api_token"`
		Channel string
		Ignore  []string
	}
}

func exit(err error) {
	fmt.Printf("ERROR: %s\n", err)
	os.Exit(1)
}

func ircBot() {

	channel := config.IRC.Channel
	privacy := config.IRC.Privacy

	// Configure the connection.
	conn := irc.IRC(config.IRC.Nick, config.IRC.Nick)
	conn.QuitMessage = config.IRC.QuitMsg

	if config.IRC.TLS {
		conn.TLSConfig = &tls.Config{ServerName: config.IRC.Server}
		conn.UseTLS = true
	}

	// Add callback to identify with auth providers and join the channel as soon
	// as a connection is established.
	conn.AddCallback("001", func(e *irc.Event) {
		if config.IRC.Auth.Type == "nickserv" {
			conn.Privmsgf("nickserv", "identify %s %s", config.IRC.Nick, config.IRC.Auth.Password)
		}
		conn.Join(channel)
	})

	handleMsg := func(e *irc.Event) {
		if len(e.Arguments) != 2 {
			return
		}
		if e.Arguments[0] != channel {
			return
		}
		if e.Code == "PRIVMSG" {
			if privacy && strings.HasPrefix(e.Arguments[1], "#") {
				return
			}
			ircMsgs <- fmt.Sprintf("<%s> %s", e.Nick, e.Arguments[1])
		} else {
			ircMsgs <- fmt.Sprintf("* %s %s", e.Nick, e.Arguments[1])
		}
	}

	conn.AddCallback("PRIVMSG", handleMsg)
	conn.AddCallback("CTCP_ACTION", handleMsg)

	// Attempt the connection to the IRC server.
	err := conn.Connect(fmt.Sprintf("%s:%d", config.IRC.Server, config.IRC.Port))
	if err != nil {
		exit(err)
	}

	// Close the connection on Ctrl-C.
	process.SetExitHandler(func() {
		fmt.Println("Quiting IRC ...")
		conn.Quit()
	})

	// Post Slack messages as they arrive.
	for msg := range slackMsgs {
		if len(msg) > 350 {
			msg = msg[:350]
			if msg[349] == ' ' {
				msg += "... [truncated]"
			} else {
				msg += " ... [truncated]"
			}
		}
		conn.Privmsg(channel, msg)
	}

}

func slackBot() {

	client := slack.New(config.Slack.API)
	channel := stripHash(config.Slack.Channel)
	channelID := ""
	users := map[string]string{}

	go func() {
		params := slack.PostMessageParameters{
			AsUser: true,
		}
		for msg := range ircMsgs {
			client.PostMessage(channel, msg, params)
		}
	}()

	ignore := map[string]bool{}
	for _, user := range config.Slack.Ignore {
		ignore[strings.ToLower(user)] = true
	}

	self, err := client.AuthTest()
	if err != nil {
		exit(err)
	}

	selfID := self.UserID
	rtm := client.NewRTM()
	go rtm.ManageConnection()

	for msg := range rtm.IncomingEvents {
		switch e := msg.Data.(type) {
		case *slack.MessageEvent:
			if e.Hidden {
				break
			}
			if e.SubType != "" && e.SubType != "me_message" {
				break
			}
			if e.User == selfID {
				break
			}
			if channelID == "" {
				info, err := client.GetChannelInfo(e.Channel)
				if err != nil {
					fmt.Printf("ERROR: Unable to get channel info for %s: %s", e.Channel, err)
					break
				}
				if info.Name == channel {
					channelID = e.Channel
				}
			}
			if e.Channel != channelID {
				break
			}
			user, exists := users[e.User]
			if !exists {
				info, err := client.GetUserInfo(e.User)
				if err != nil {
					fmt.Printf("ERROR: Unable to get user info for %s: %s", e.User, err)
					break
				}
				user = info.Name
				users[e.User] = info.Name
			}
			if ignore[strings.ToLower(user)] {
				break
			}
			if e.SubType == "" {
				slackMsgs <- fmt.Sprintf("<%s> %s", user, e.Text)
			} else if e.SubType == "me_message" {
				slackMsgs <- fmt.Sprintf("* %s %s", user, e.Text)
			}
		case *slack.InvalidAuthEvent:
			exit(errors.New("slack: invalid auth credentials"))
		case *slack.RTMError:
			fmt.Printf("ERROR: %s\n", e.Error())
		}
	}

}

func stripHash(channel string) string {
	if strings.HasPrefix(channel, "#") {
		return channel[1:]
	}
	return channel
}

func main() {

	opts := optparse.New("Usage: irc-slack path/to/config.yaml")
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

	<-make(chan struct{})

}
