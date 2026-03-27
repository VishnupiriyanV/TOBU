import { useState, useEffect } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import './CustomPdfViewer.css';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

// Configure the worker explicitly for react-pdf to work seamlessly in Vite
pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString();

export default function CustomPdfViewer({ fileUrl, onClose, initialPage = 1, timestamp = null }) {
  const [numPages, setNumPages] = useState(null);
  const [pageNumber, setPageNumber] = useState(initialPage);
  const [loading, setLoading] = useState(true);

  // When timestamp changes, try to jump to related page
  // A rough heuristic: if we have a timestamp like 30s, and we know page average,
  // or we just map timestamp seconds roughly to page (since many document matching chunks report timestamp as page index or similar).
  // Often in document search, 'start' might literally be the page number. 
  useEffect(() => {
    if (timestamp !== null && timestamp !== undefined) {
      // If timestamp is like 1, 2, 3... it might be the page number
      // So we set the page number to match it (bounded between 1 and numPages)
      const targetPage = Math.max(1, Math.floor(timestamp));
      setPageNumber(targetPage);
    }
  }, [timestamp]);

  function onDocumentLoadSuccess({ numPages }) {
    setNumPages(numPages);
    setLoading(false);
    // Ensure pageNumber is within bounds
    setPageNumber((prev) => Math.min(Math.max(1, prev), numPages));
  }

  function goToPrevPage() {
    setPageNumber((prev) => Math.max(prev - 1, 1));
  }

  function goToNextPage() {
    setPageNumber((prev) => Math.min(prev + 1, numPages || 1));
  }

  return (
    <div className="custom-pdf-viewer">
      <div className="pdf-toolbar">
        <div className="pdf-toolbar-left">
          <span className="material-symbols-outlined" style={{ color: '#f87171' }}>picture_as_pdf</span>
          <span className="pdf-title font-mono">PDF Document</span>
        </div>
        
        <div className="pdf-controls font-mono">
          <button onClick={goToPrevPage} disabled={pageNumber <= 1} className="pdf-btn">
            <span className="material-symbols-outlined">chevron_left</span>
          </button>
          <span className="pdf-page-indicator">
            {pageNumber} / {numPages || '?'}
          </span>
          <button onClick={goToNextPage} disabled={pageNumber >= numPages} className="pdf-btn">
            <span className="material-symbols-outlined">chevron_right</span>
          </button>
        </div>

        <button className="pdf-close-btn" onClick={onClose} title="Close PDF Viewer">
          <span className="material-symbols-outlined">close</span>
        </button>
      </div>

      <div className="pdf-document-container">
        {loading && <div className="pdf-loading">Loading PDF...</div>}
        <Document
          file={fileUrl}
          onLoadSuccess={onDocumentLoadSuccess}
          loading=""
          error={<div className="pdf-error">Failed to load PDF file.</div>}
        >
          {numPages && (
            <Page 
              pageNumber={pageNumber} 
              renderTextLayer={true}
              renderAnnotationLayer={true}
              className="pdf-page"
              width={undefined} // Let CSS handle responsiveness if needed, or leave default
            />
          )}
        </Document>
      </div>
    </div>
  );
}
