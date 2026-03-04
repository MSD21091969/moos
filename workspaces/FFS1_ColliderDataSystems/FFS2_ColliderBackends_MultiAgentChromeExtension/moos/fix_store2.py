import os
import re

path = r"internal/container/store.go"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

# Find the end of GenerateUUID()
idx = text.find("return fmt.Sprintf(")
end_idx = text.find("}\n", idx) + 2

clean_text = text[:end_idx]

clean_text += '''
func (store *Store) ListByKind(ctx context.Context, kind string, limit int) ([]Record, error) {
\trows, err := store.db.QueryContext(ctx,
\t\tSELECT urn, parent_urn, kind, interface_json, kernel_json, permissions_json, version
\t\tFROM containers
\t\tWHERE kind = 
\t\tORDER BY updated_at DESC
\t\tLIMIT , kind, limit)
\tif err != nil {
\t\treturn nil, err
\t}
\tdefer rows.Close()

\tresult := make([]Record, 0)
\tfor rows.Next() {
\t\tvar rec Record
\t\tif err := rows.Scan(&rec.URN, &rec.ParentURN, &rec.Kind, &rec.InterfaceJSON, &rec.KernelJSON, &rec.PermissionsJSON, &rec.Version); err != nil {
\t\t\treturn nil, err
\t\t}
\t\tresult = append(result, rec)
\t}
\treturn result, rows.Err()
}
'''

with open(path, "w", encoding="utf-8") as f:
    f.write(clean_text)
print("fixed store.go fully")
