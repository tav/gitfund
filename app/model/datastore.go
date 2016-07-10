// Public Domain (-) 2016 The GitFund Authors.
// See the GitFund UNLICENSE file for details.

package model

import (
	"context"
	"errors"
	"math"
	"time"

	"github.com/tav/gitfund/app/config"
	"google.golang.org/cloud/datastore"
)

var ErrLimitNotSet = errors.New("datastore: neither Limit nor NoLimit have been called on Query")

// Key provides a unified interface for datastore.Key and datastore.PendingKey
// so as to simplify the creation and use of keys in datastore operations.
//
// Do not access the Datastore and Pending struct fields of Keys from
// application code. They are only exposed for use by utility methods on
// web.Context.
type Key struct {
	Datastore *datastore.Key
	Pending   *datastore.PendingKey
}

func (k *Key) Equal(o *Key) bool {
	return k.Datastore.Equal(o.Datastore)
}

func (k *Key) ID() int64 {
	return k.Datastore.ID()
}

func (k *Key) Incomplete() bool {
	return k.Datastore.Incomplete()
}

func (k *Key) Kind() string {
	return k.Datastore.Kind()
}

func (k *Key) Name() string {
	return k.Datastore.Name()
}

func (k *Key) Parent() *Key {
	return &Key{Datastore: k.Datastore.Parent()}
}

func (k *Key) SetParent(p *Key) {
	k.Datastore.SetParent(p.Datastore)
}

func (k *Key) String() string {
	return k.Datastore.String()
}

// Do not instantiate Query directly. Instead, use the utility constructors
// provided on web.Context, i.e.
//
//	q := c.Query("User")
//
// Or, even better still, the specific constructor for the model kind, e.g.
//
//	q := c.UserQuery()
//
// Special care should be taken to ensure that transactional queries are
// instantiated within the related transaction handler, e.g.
//
//	err := c.Transact(func (c *web.Context) error {
//		query := c.Query("User")
//		// use query ...
//	})
//
// And not:
//
//  query := c.Query("User")
//	err := c.Transact(func (c *web.Context) error {
//		// use query ...
//	})
//
// Otherwise, the query will not be associated with the running transaction and
// the results will not be consistent with the rest of the transaction.
type Query struct {
	ctx     context.Context
	limset  bool
	query   *datastore.Query
	timeout time.Duration
}

func (q *Query) Ancestor(ancestor *datastore.Key) *Query {
	return &Query{q.ctx, q.limset, q.query.Ancestor(ancestor), q.timeout}
}

func (q *Query) End(c datastore.Cursor) *Query {
	return &Query{q.ctx, q.limset, q.query.End(c), q.timeout}
}

func (q *Query) EventualConsistency() *Query {
	return &Query{q.ctx, q.limset, q.query.EventualConsistency(), q.timeout}
}

func (q *Query) Filter(filterStr string, value interface{}) *Query {
	return &Query{q.ctx, q.limset, q.query.Filter(filterStr, value), q.timeout}
}

func (q *Query) GetAll(dst interface{}) ([]*datastore.Key, error) {
	if err := q.validate(); err != nil {
		return nil, err
	}
	ctx, cancel := q.getContextCanceler()
	keys, err := config.DataClient.GetAll(ctx, q.query, dst)
	cancel()
	return keys, err
}

func (q *Query) getContextCanceler() (context.Context, context.CancelFunc) {
	if q.timeout == 0 {
		// Since timeout being 0 is used to indicate that we are within a
		// transaction handler, the context would have already had a timeout
		// set. So don't bother creating a new one.
		return q.ctx, dummyCancel
	}
	return context.WithTimeout(q.ctx, q.timeout)
}

func (q *Query) GetCount() (int, error) {
	if err := q.validate(); err != nil {
		return 0, err
	}
	ctx, cancel := q.getContextCanceler()
	count, err := config.DataClient.Count(ctx, q.query)
	cancel()
	return count, err
}

func (q *Query) KeysOnly() *Query {
	return &Query{q.ctx, q.limset, q.query.KeysOnly(), q.timeout}
}

func (q *Query) Limit(limit int) *Query {
	return &Query{q.ctx, true, q.query.Limit(limit), q.timeout}
}

func (q *Query) NoLimit() *Query {
	return &Query{q.ctx, true, q.query.Limit(math.MaxInt32), q.timeout}
}

func (q *Query) Order(fieldName string) *Query {
	return &Query{q.ctx, q.limset, q.query.Order(fieldName), q.timeout}
}

func (q *Query) Run() (*datastore.Iterator, error) {
	if err := q.validate(); err != nil {
		return nil, err
	}
	ctx, cancel := q.getContextCanceler()
	iter := config.DataClient.Run(ctx, q.query)
	cancel()
	return iter, nil
}

func (q *Query) Start(c datastore.Cursor) *Query {
	return &Query{q.ctx, q.limset, q.query.Start(c), q.timeout}
}

func (q *Query) Timeout(d time.Duration) *Query {
	return &Query{q.ctx, q.limset, q.query, d}
}

func (q *Query) validate() error {
	if !q.limset {
		return ErrLimitNotSet
	}
	return nil
}

// NewQuery wraps a datastore.Query with an associated context to create a new
// Query.
//
// Do not call this from application code. The constructor is only exposed for
// use by web.Context. Use the Query constructor methods on that instead.
func NewQuery(c context.Context, q *datastore.Query, timeout time.Duration) *Query {
	return &Query{
		ctx:     c,
		query:   q,
		timeout: timeout,
	}
}

func dummyCancel() {}
