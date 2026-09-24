"use client";

import React, { useCallback, useRef, useState } from "react";
import { getDestinationImages } from "../destinationImages";
import { X, Upload, Image as ImageIcon, Globe } from "lucide-react";

type ImageTab = "upload" | "media" | "destination";

interface ImageChangerPanelProps {
  sectionLabel: string;
  destination: string;
  currentImage: string;
  onApply: (url: string) => void;
  onClose: () => void;
}

export default function ImageChangerPanel({
  sectionLabel,
  destination,
  currentImage,
  onApply,
  onClose,
}: ImageChangerPanelProps) {
  const [activeTab, setActiveTab] = useState<ImageTab>("upload");
  const [selectedImage, setSelectedImage] = useState<string>(currentImage);
  const [dragOver, setDragOver] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const destinationImages = getDestinationImages(destination);

  const handleFileChange = useCallback((file: File) => {
    if (!file.type.startsWith("image/")) return;
    if (file.size > 10 * 1024 * 1024) {
      alert("File too large. Maximum size is 10MB.");
      return;
    }
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    setSelectedImage(url);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleFileChange(file);
  }, [handleFileChange]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFileChange(file);
  };

  const handleApply = () => {
    if (selectedImage) {
      onApply(selectedImage);
    }
  };

  return (
    <div className="ps-image-panel">
      {/* Header */}
      <div className="ps-image-panel-header">
        <div className="ps-image-panel-title">
          <ImageIcon size={16} strokeWidth={2} />
          <span>Change {sectionLabel} Image</span>
        </div>
        <button className="ps-panel-close" onClick={onClose} aria-label="Close image panel">
          <X size={16} />
        </button>
      </div>

      {/* Tabs */}
      <div className="ps-image-tabs">
        <button
          className={`ps-image-tab ${activeTab === "upload" ? "active" : ""}`}
          onClick={() => setActiveTab("upload")}
        >
          <Upload size={13} /> Upload
        </button>
        <button
          className={`ps-image-tab ${activeTab === "media" ? "active" : ""}`}
          onClick={() => setActiveTab("media")}
        >
          <ImageIcon size={13} /> Media Library
        </button>
        <button
          className={`ps-image-tab ${activeTab === "destination" ? "active" : ""}`}
          onClick={() => setActiveTab("destination")}
        >
          <Globe size={13} /> Destination Images
        </button>
      </div>

      {/* Tab Content */}
      <div className="ps-image-panel-body">
        {activeTab === "upload" && (
          <div
            className={`ps-drop-zone ${dragOver ? "drag-over" : ""}`}
            onDrop={handleDrop}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onClick={() => fileInputRef.current?.click()}
          >
            <Upload size={28} strokeWidth={1.5} />
            <p className="ps-drop-title">Drag and drop an image here</p>
            <p className="ps-drop-sub">or click to upload</p>
            <p className="ps-drop-hint">Supports JPG, PNG, WEBP (Max 10MB)</p>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              style={{ display: "none" }}
              onChange={handleInputChange}
            />
          </div>
        )}

        {activeTab === "media" && (
          <div className="ps-media-library">
            <div className="ps-media-empty">
              <ImageIcon size={32} strokeWidth={1.2} />
              <p>Your uploaded images will appear here.</p>
              <button
                className="ps-btn-outline"
                onClick={() => setActiveTab("upload")}
              >
                Upload an Image
              </button>
            </div>
          </div>
        )}

        {activeTab === "destination" && (
          <div>
            <p className="ps-dest-label">Recommended Images ({destination || "India"})</p>
            <div className="ps-dest-grid">
              {destinationImages.map((img) => (
                <div
                  key={img.id}
                  className={`ps-dest-img-wrap ${selectedImage === img.url ? "selected" : ""}`}
                  onClick={() => setSelectedImage(img.url)}
                  title={img.label}
                >
                  <img src={img.url} alt={img.alt} className="ps-dest-img" loading="lazy" />
                  {selectedImage === img.url && (
                    <div className="ps-dest-check">✓</div>
                  )}
                  <div className="ps-dest-img-label">{img.label}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Preview if upload selected */}
        {previewUrl && activeTab === "upload" && (
          <div className="ps-upload-preview">
            <img src={previewUrl} alt="Preview" className="ps-upload-preview-img" />
            <p className="ps-upload-preview-label">Ready to apply</p>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="ps-image-panel-footer">
        <button className="ps-btn-ghost" onClick={onClose}>Cancel</button>
        <button
          className="ps-btn-gold"
          onClick={handleApply}
          disabled={!selectedImage}
        >
          Apply Image
        </button>
      </div>
    </div>
  );
}
