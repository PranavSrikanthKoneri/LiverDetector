import { useState, useRef } from "react";
import { UploadIcon, ArchiveIcon, Cross2Icon, ArrowRightIcon } from "@radix-ui/react-icons";
import "./UploadPage.css";

export default function UploadPage({ onNext }) {
  const [file, setFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef(null);

  function handleDrag(e) {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") setDragActive(true);
    if (e.type === "dragleave") setDragActive(false);
  }

  function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files?.[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  }

  function handleFileChange(e) {
    if (e.target.files?.[0]) {
      setFile(e.target.files[0]);
    }
  }

  function handleRemove() {
    setFile(null);
    if (inputRef.current) inputRef.current.value = "";
  }

  return (
    <div className="page">
      <div className="container stack stack-xl">
        <div className="upload-hero">
          <h2>Upload MRI Data</h2>
          <p className="text-secondary">
            Upload DICOM .zip archive (in-phase and opposed-phase).
          </p>
        </div>

        <div
          className={`upload-dropzone card ${
            dragActive ? "drag-active" : ""
          } ${file ? "has-file" : ""}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => !file && inputRef.current?.click()}
          id="mri-upload-dropzone"
        >
          <input
            ref={inputRef}
            type="file"
            accept=".zip"
            onChange={handleFileChange}
            className="sr-only"
            id="mri-file-input"
          />

          {!file ? (
            <div className="upload-dropzone-content">
              <div className="upload-icon-ring">
                <UploadIcon width={24} height={24} />
              </div>
              <p className="upload-dropzone-title">
                Drop DICOM archive here
              </p>
              <p className="text-tertiary" style={{ fontSize: "0.8125rem" }}>
                or click to browse
              </p>
            </div>
          ) : (
            <div className="upload-file-info">
              <div className="upload-file-icon">
                <ArchiveIcon width={20} height={20} />
              </div>
              <div className="upload-file-details">
                <span className="upload-file-name">{file.name}</span>
                <span className="text-tertiary" style={{ fontSize: "0.75rem" }}>
                  {(file.size / (1024 * 1024)).toFixed(1)} MB
                </span>
              </div>
              <button
                className="btn btn-ghost btn-sm"
                onClick={(e) => {
                  e.stopPropagation();
                  handleRemove();
                }}
                aria-label="Remove file"
                id="remove-file-btn"
              >
                <Cross2Icon width={16} height={16} />
              </button>
            </div>
          )}
        </div>

        <div className="upload-actions">
          <button
            className="btn btn-primary btn-lg"
            onClick={() => onNext(file)}
            disabled={!file || !file.name.toLowerCase().endsWith('.zip')}
            id="upload-continue-btn"
          >
            Continue
            <ArrowRightIcon width={18} height={18} />
          </button>
          <p className="text-tertiary" style={{ fontSize: "0.75rem", textAlign: "center" }}>
            Select a ZIP containing in-phase and opposed-phase DICOM images.
          </p>
        </div>
      </div>
    </div>
  );
}
