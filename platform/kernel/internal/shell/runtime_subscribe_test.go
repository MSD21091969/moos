package shell_test

import (
	"fmt"
	"testing"
	"time"

	"moos/platform/kernel/internal/cat"
)

func TestSubscribeBroadcast(t *testing.T) {
	rt := newTestRuntime(t)
	_, ch := rt.Subscribe()

	env := cat.Envelope{
		Type:  cat.ADD,
		Actor: testActor,
		Add:   &cat.AddPayload{URN: "urn:moos:test:broadcast", TypeID: "node_container"},
	}
	if _, err := rt.Apply(env); err != nil {
		t.Fatalf("Apply: %v", err)
	}

	select {
	case got := <-ch:
		if got.Envelope.Add == nil {
			t.Fatal("expected Add payload in broadcast")
		}
		if got.Envelope.Add.URN != "urn:moos:test:broadcast" {
			t.Fatalf("expected urn:moos:test:broadcast, got %s", got.Envelope.Add.URN)
		}
	case <-time.After(time.Second):
		t.Fatal("no broadcast received within 1s")
	}
}

func TestUnsubscribe(t *testing.T) {
	rt := newTestRuntime(t)
	id, ch := rt.Subscribe()
	rt.Unsubscribe(id)

	// Channel should be closed after unsubscribe.
	_, ok := <-ch
	if ok {
		t.Fatal("expected channel to be closed after Unsubscribe")
	}
}

func TestSlowSubscriber(t *testing.T) {
	rt := newTestRuntime(t)
	rt.Subscribe() // subscribe but never read — intentionally slow

	done := make(chan struct{})
	go func() {
		for i := 0; i < 100; i++ {
			env := cat.Envelope{
				Type:  cat.ADD,
				Actor: testActor,
				Add: &cat.AddPayload{
					URN:    cat.URN(fmt.Sprintf("urn:moos:test:slow-%d", i)),
					TypeID: "node_container",
				},
			}
			if _, err := rt.Apply(env); err != nil {
				// node_container count limit may be hit; that's fine — we're testing
				// that Apply never blocks regardless.
				_ = err
			}
		}
		close(done)
	}()

	select {
	case <-done:
		// Kernel did not block on slow subscriber — pass.
	case <-time.After(5 * time.Second):
		t.Fatal("kernel blocked by slow subscriber for too long")
	}
}
