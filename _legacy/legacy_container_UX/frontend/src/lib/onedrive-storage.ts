import { Client } from '@microsoft/microsoft-graph-client';
import { getAccessToken } from './microsoft-auth';

const WORKSPACE_FILE_NAME = 'collider-workspace.json';
const APP_FOLDER = '/me/drive/special/approot';
const TEMP_EDIT_FOLDER = 'Collider_Temp_Edits';

export interface OneDriveFile {
    id: string;
    name: string;
    webUrl: string;
    lastModifiedDateTime: string;
    eTag: string;
}

// Initialize Graph client
function getGraphClient() {
  return Client.init({
    authProvider: async (done) => {
      try {
        const token = await getAccessToken();
        done(null, token);
      } catch (error) {
        done(error, null);
      }
    },
  });
}

// Save workspace to OneDrive
export async function saveWorkspaceToOneDrive(workspaceData: any) {
  const client = getGraphClient();
  
  try {
    const content = JSON.stringify(workspaceData);
    await client
      .api(`${APP_FOLDER}/${WORKSPACE_FILE_NAME}:/content`)
      .put(content);
    
    console.log('✅ Workspace saved to OneDrive');
    return true;
  } catch (error) {
    console.error('❌ OneDrive save failed:', error);
    throw error;
  }
}

// Load workspace from OneDrive
export async function loadWorkspaceFromOneDrive() {
  const client = getGraphClient();
  
  try {
    const response = await client
      .api(`${APP_FOLDER}/${WORKSPACE_FILE_NAME}:/content`)
      .get();
    
    console.log('✅ Workspace loaded from OneDrive');
    return JSON.parse(response);
  } catch (error: any) {
    if (error.statusCode === 404) {
      console.log('📦 No workspace found in OneDrive (first time)');
      return null;
    }
    console.error('❌ OneDrive load failed:', error);
    throw error;
  }
}

/**
 * CHECK-OUT: Uploads a file to a temp folder in OneDrive for editing.
 * Returns the file metadata including the webUrl for Office Online.
 */
export async function checkOutFile(fileName: string, content: Blob): Promise<OneDriveFile> {
    const client = getGraphClient();
    try {
        // Upload to a specific temp folder to avoid clutter
        // Note: The folder will be auto-created if it doesn't exist
        const uploadPath = `${APP_FOLDER}/${TEMP_EDIT_FOLDER}/${fileName}:/content`;
        
        console.log(`📤 Uploading ${fileName} to OneDrive...`);
        const response = await client.api(uploadPath).put(content);
        
        console.log('✅ File uploaded to OneDrive:', response.id);
        
        return {
            id: response.id,
            name: response.name,
            webUrl: response.webUrl,
            lastModifiedDateTime: response.lastModifiedDateTime,
            eTag: response.eTag
        };
    } catch (error) {
        console.error('❌ Check-out failed:', error);
        throw error;
    }
}

/**
 * CHECK-IN: Downloads the file back from OneDrive and deletes the temp copy.
 */
export async function checkInFile(fileId: string): Promise<Blob> {
    const client = getGraphClient();
    try {
        console.log(`📥 Downloading ${fileId} from OneDrive...`);
        
        // 1. Download content
        // We use responseType: 'blob' to get binary data
        const response = await client
            .api(`/me/drive/items/${fileId}/content`)
            .responseType('arraybuffer' as any)
            .get();
            
        // 2. Delete file (cleanup)
        console.log(`🗑️ Cleaning up ${fileId}...`);
        await client.api(`/me/drive/items/${fileId}`).delete();
        
        return response;
    } catch (error) {
        console.error('❌ Check-in failed:', error);
        throw error;
    }
}

/**
 * Get file metadata (useful for checking if file was modified).
 */
export async function getFileMetadata(fileId: string): Promise<OneDriveFile> {
     const client = getGraphClient();
     try {
         const response = await client.api(`/me/drive/items/${fileId}`).get();
         return {
            id: response.id,
            name: response.name,
            webUrl: response.webUrl,
            lastModifiedDateTime: response.lastModifiedDateTime,
            eTag: response.eTag
        };
     } catch (error) {
         console.error('❌ Failed to get metadata:', error);
         throw error;
     }
}

// Legacy upload (kept for backward compatibility if needed, but checkOutFile is preferred)
export async function uploadFileToOneDrive(fileName: string, content: string | Blob, contentType: string) {
    const client = getGraphClient();
    try {
        const response = await client
            .api(`${APP_FOLDER}/${fileName}:/content`)
            .header('Content-Type', contentType)
            .put(content);
        
        const item = await client.api(response.id).get();
        return item.webUrl;
    } catch (error) {
        console.error('❌ File upload failed:', error);
        throw error;
    }
}
