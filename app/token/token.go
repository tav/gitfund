// Public Domain (-) 2016 The GitFund Authors.
// See the GitFund UNLICENSE file for details.

package token

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
	ID   int
}

type Keys map[int]*KeySpec

type Signed struct {
	spec  *KeySpec
	state *state
}

func (t *Signed) String() string {
	j, err := json.MarshalIndent(t.state, "", "")
	if err != nil {
		panic(err)
	}
	mac := hmac.New(t.spec.Hash, t.spec.Key)
	_, err = mac.Write(j)
	if err != nil {
		panic(err)
	}
	digest := mac.Sum(nil)
	return fmt.Sprintf("%x.%x.%x.%x", t.spec.ID, digest, t.state.Value, t.state.Expires)
}

type state struct {
	Name    string `json:"c"`
	Value   string `json:"v"`
	Expires int64  `json:"e"`
}

func New(name string, value string, duration time.Duration, spec *KeySpec) *Signed {
	return &Signed{
		spec: spec,
		state: &state{
			Name:    name,
			Value:   value,
			Expires: time.Now().UTC().Add(duration).Unix(),
		},
	}
}

func Parse(name string, token string, keys Keys) string {
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
	spec, exists := keys[int(keyID)]
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
	s := &state{
		Name:    name,
		Value:   string(value),
		Expires: expires,
	}
	j, err := json.MarshalIndent(s, "", "")
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
		return s.Value
	}
	return ""
}
