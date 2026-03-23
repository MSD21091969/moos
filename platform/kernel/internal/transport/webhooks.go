package transport

import (
"encoding/json"
"net/http"
"time"

"moos/platform/kernel/internal/cat"
"moos/platform/kernel/internal/shell"
)

// HandleGCalWebhook processes incoming Google Calendar events and injects them into the hyperspace as SOT.
func HandleGCalWebhook(rt *shell.Runtime) http.HandlerFunc {
return func(w http.ResponseWriter, r *http.Request) {
// Example right-adjoint integration logic
var payload map[string]interface{}
if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
http.Error(w, "Bad Request", http.StatusBadRequest)
return
}

// Hydrate GCal -> Graph
env := cat.Envelope{
Type:  cat.ADD,
Actor: "urn:moos:agent:gcal-sync",
Add: &cat.AddPayload{
URN:     cat.URN("urn:moos:event:gcal-" + time.Now().Format("20060102150405")),
TypeID:  "calendar_event",
Stratum: "S2",
Payload: payload,
},
}

if _, err := rt.Apply(env); err != nil {
http.Error(w, "State Application Failed", http.StatusInternalServerError)
return
}

w.WriteHeader(http.StatusAccepted)
}
}

