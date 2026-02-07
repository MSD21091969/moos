$project = "mailmind-ai-djbuw"
$database = "my-tiny-data-collider"

Write-Host "Creating Firestore Indexes for $project / $database..."

# sessions: acl.owner ASC, depth ASC
Write-Host "Creating index: sessions (acl.owner ASC, depth ASC)"
gcloud firestore indexes composite create --project=$project --database=$database --collection-group=sessions --field-config "field-path=acl.owner,order=ascending" --field-config "field-path=depth,order=ascending" --async

# sessions: acl.editors CONTAINS, depth ASC
Write-Host "Creating index: sessions (acl.editors CONTAINS, depth ASC)"
gcloud firestore indexes composite create --project=$project --database=$database --collection-group=sessions --field-config "field-path=acl.editors,array-config=contains" --field-config "field-path=depth,order=ascending" --async

# sessions: acl.viewers CONTAINS, depth ASC
Write-Host "Creating index: sessions (acl.viewers CONTAINS, depth ASC)"
gcloud firestore indexes composite create --project=$project --database=$database --collection-group=sessions --field-config "field-path=acl.viewers,array-config=contains" --field-config "field-path=depth,order=ascending" --async

# usersessions: user_id ASC, created_at DESC
Write-Host "Creating index: usersessions (user_id ASC, created_at DESC)"
gcloud firestore indexes composite create --project=$project --database=$database --collection-group=usersessions --field-config "field-path=user_id,order=ascending" --field-config "field-path=created_at,order=descending" --async

# sessions: user_id ASC, status ASC
Write-Host "Creating index: sessions (user_id ASC, status ASC)"
gcloud firestore indexes composite create --project=$project --database=$database --collection-group=sessions --field-config "field-path=user_id,order=ascending" --field-config "field-path=status,order=ascending" --async

# events: timestamp ASC (Collection Group)
Write-Host "Creating index: events (timestamp ASC) [COLLECTION_GROUP]"
gcloud firestore indexes composite create --project=$project --database=$database --collection-group=events --query-scope=COLLECTION_GROUP --field-config "field-path=timestamp,order=ascending" --async

# events: depth ASC, timestamp ASC (Collection Group)
Write-Host "Creating index: events (depth ASC, timestamp ASC) [COLLECTION_GROUP]"
gcloud firestore indexes composite create --project=$project --database=$database --collection-group=events --query-scope=COLLECTION_GROUP --field-config "field-path=depth,order=ascending" --field-config "field-path=timestamp,order=ascending" --async

# quota: user_id ASC, date DESC
Write-Host "Creating index: quota (user_id ASC, date DESC)"
gcloud firestore indexes composite create --project=$project --database=$database --collection-group=quota --field-config "field-path=user_id,order=ascending" --field-config "field-path=date,order=descending" --async

# quota: user_id ASC, date ASC
Write-Host "Creating index: quota (user_id ASC, date ASC)"
gcloud firestore indexes composite create --project=$project --database=$database --collection-group=quota --field-config "field-path=user_id,order=ascending" --field-config "field-path=date,order=ascending" --async

Write-Host "Index creation initiated. Check status in GCP Console."
