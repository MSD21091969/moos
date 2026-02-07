/**
 * Office Online Viewer integration
 * Opens Office files (Word, Excel, PowerPoint) in browser using Office Online
 */

export type OfficeViewerMode = 'view' | 'edit';

export interface OfficeViewerOptions {
  /** Signed URL to the file */
  fileUrl: string;
  /** View (read-only) or edit mode */
  mode: OfficeViewerMode;
  /** Optional: Override viewer base URL */
  viewerBaseUrl?: string;
}

/**
 * Open file in Office Online viewer
 * 
 * @param options - Viewer configuration
 * @returns Window reference (for potential postMessage communication)
 * 
 * @example
 * ```typescript
 * const signedUrl = await getSignedUrlFromBackend(fileId);
 * openInOfficeOnline({ fileUrl: signedUrl, mode: 'view' });
 * ```
 */
export function openInOfficeOnline(options: OfficeViewerOptions): Window | null {
  const {
    fileUrl,
    mode = 'view',
    viewerBaseUrl = 'https://view.officeapps.live.com',
  } = options;

  // Encode the file URL for Office Online
  const encodedUrl = encodeURIComponent(fileUrl);
  
  // Construct Office Online viewer URL
  // Format: https://view.officeapps.live.com/op/{action}.aspx?src={encodedUrl}
  const action = mode === 'edit' ? 'edit' : 'view';
  const viewerUrl = `${viewerBaseUrl}/op/${action}.aspx?src=${encodedUrl}`;

  // Open in new tab
  const windowRef = window.open(viewerUrl, '_blank', 'noopener,noreferrer');

  if (!windowRef) {
    console.error('Failed to open Office Online viewer - popup blocked?');
    return null;
  }

  return windowRef;
}

/**
 * Check if file type is supported by Office Online
 * 
 * @param filename - File name or path
 * @returns True if file type is supported
 */
export function isOfficeFileType(filename: string): boolean {
  const ext = filename.toLowerCase().split('.').pop();
  
  const supportedExtensions = [
    // Word
    'doc', 'docx', 'docm', 'dot', 'dotx', 'dotm',
    // Excel
    'xls', 'xlsx', 'xlsm', 'xlsb', 'xlt', 'xltx', 'xltm',
    // PowerPoint
    'ppt', 'pptx', 'pptm', 'pot', 'potx', 'potm', 'pps', 'ppsx', 'ppsm',
    // Other
    'odt', 'ods', 'odp', // OpenDocument
  ];

  return supportedExtensions.includes(ext || '');
}

/**
 * Get file icon name for Office files
 * 
 * @param filename - File name or path
 * @returns Lucide icon name
 */
export function getOfficeFileIcon(filename: string): string {
  const ext = filename.toLowerCase().split('.').pop();

  switch (ext) {
    case 'doc':
    case 'docx':
    case 'docm':
    case 'dot':
    case 'dotx':
    case 'dotm':
    case 'odt':
      return 'FileText';
    
    case 'xls':
    case 'xlsx':
    case 'xlsm':
    case 'xlsb':
    case 'xlt':
    case 'xltx':
    case 'xltm':
    case 'ods':
      return 'Table';
    
    case 'ppt':
    case 'pptx':
    case 'pptm':
    case 'pot':
    case 'potx':
    case 'potm':
    case 'pps':
    case 'ppsx':
    case 'ppsm':
    case 'odp':
      return 'Presentation';
    
    default:
      return 'File';
  }
}

/**
 * Open file in Office Online with error handling
 * 
 * @param fileUrl - Signed URL to file
 * @param mode - Viewer mode
 * @param onError - Error callback
 */
export async function openOfficeFileWithErrorHandling(
  fileUrl: string,
  mode: OfficeViewerMode = 'view',
  onError?: (error: Error) => void
): Promise<void> {
  try {
    const windowRef = openInOfficeOnline({ fileUrl, mode });
    
    if (!windowRef) {
      throw new Error(
        'Failed to open Office Online viewer. Please disable popup blocker.'
      );
    }
    
    // Optional: Check if window closed immediately (blocked)
    setTimeout(() => {
      if (windowRef.closed) {
        const error = new Error('Office Online viewer was blocked or closed');
        if (onError) onError(error);
      }
    }, 1000);
    
  } catch (error) {
    console.error('Error opening Office Online:', error);
    if (onError && error instanceof Error) {
      onError(error);
    }
  }
}
