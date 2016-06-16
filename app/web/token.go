// Public Domain (-) 2016 The Gitfund Authors.
// See the Gitfund UNLICENSE file for details.

package web

import (
	"crypto/hmac"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"hash"
	"strconv"
	"strings"
	"time"
)

type KeySpec struct {
	Key  []byte
	Hash func() hash.Hash
}

type TokenKeys map[int]*KeySpec

type Token struct {
	s *tokenState
}

func (t *Token) String() string {
	j, err := json.MarshalIndent(t.s, "", "")
	if err != nil {
		panic(err)
	}
	mac := hmac.New(tokenHash, tokenKey)
	_, err = mac.Write(j)
	if err != nil {
		panic(err)
	}
	digest := mac.Sum(nil)
	return fmt.Sprintf("%x.%x.%x.%x", tokenKeyID, digest, t.s.Value, t.s.Expires)
}

type tokenState struct {
	Context string `json:"c"`
	Value   string `json:"v"`
	Expires int64  `json:"e"`
}

func NewToken(context string, value string, duration time.Duration) *Token {
	return &Token{&tokenState{
		Context: context,
		Value:   value,
		Expires: time.Now().UTC().Add(duration).Unix(),
	}}
}

func ParseToken(context string, token string) string {
	if len(token) == 0 {
		return ""
	}
	split := strings.Split(token, ".")
	if len(split) != 4 {
		return ""
	}
	keyID, err := strconv.ParseInt(split[0], 16, 64)
	if err != nil {
		return ""
	}
	spec, exists := tokenKeys[int(keyID)]
	if !exists {
		return ""
	}
	expected, err := hex.DecodeString(split[1])
	if err != nil {
		return ""
	}
	value, err := hex.DecodeString(split[2])
	if err != nil {
		return ""
	}
	expires, err := strconv.ParseInt(split[3], 16, 64)
	if err != nil {
		return ""
	}
	if time.Unix(expires, 0).UTC().Before(time.Now().UTC()) {
		return ""
	}
	state := &tokenState{
		Context: context,
		Value:   string(value),
		Expires: expires,
	}
	j, err := json.MarshalIndent(state, "", "")
	if err != nil {
		return ""
	}
	mac := hmac.New(spec.Hash, spec.Key)
	_, err = mac.Write(j)
	if err != nil {
		return ""
	}
	digest := mac.Sum(nil)
	if hmac.Equal(digest, []byte(expected)) {
		return state.Value
	}
	return ""
}
