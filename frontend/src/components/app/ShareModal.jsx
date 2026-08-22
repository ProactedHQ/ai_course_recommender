import { useCallback } from 'react';
import { X, Download } from 'lucide-react';
import './ShareModal.css';

/* ── Platform share helpers ── */
const SITE_URL = 'https://proactedai.co.ke';
const SHARE_TEXT = 'Check out my AI-powered university course recommendations from KeDira!';

/**
 * Downloads the PNG blob to the user's device.
 */
const downloadImage = (blob, filename = 'my-kedira-recommendations.png') => {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 5000);
};

/**
 * Uses the native Web Share API (supported on mobile browsers) to share the file.
 * Falls back to downloading the image if the API is not available.
 */
const nativeShare = async (blob, platform) => {
    const file = new File([blob], 'my-kedira-recommendations.png', { type: 'image/png' });
    const canShareFile = navigator.canShare && navigator.canShare({ files: [file] });

    if (navigator.share && canShareFile) {
        try {
            await navigator.share({
                title: 'My KeDira Recommendations',
                text: SHARE_TEXT,
                files: [file],
            });
            return true;
        } catch (err) {
            if (err.name === 'AbortError') return false; // user cancelled — OK
        }
    }
    // Desktop / unsupported fallback: download the image
    downloadImage(blob);
    return false;
};

/**
 * ShareModal
 *
 * Props:
 *   imageUrl   {string}      — Object URL for <img> preview
 *   imageBlob  {Blob}        — PNG blob for share/download
 *   onClose    {function}    — close handler
 */
const ShareModal = ({ imageUrl, imageBlob, onClose }) => {

    const handleDownload = useCallback(() => {
        if (imageBlob) downloadImage(imageBlob);
    }, [imageBlob]);

    const handleWhatsApp = useCallback(async () => {
        // On mobile: native share sheet → user picks WhatsApp
        // On desktop: open wa.me with text + download image
        const shared = await nativeShare(imageBlob, 'whatsapp');
        if (!shared) {
            window.open(`https://wa.me/?text=${encodeURIComponent(SHARE_TEXT + ' ' + SITE_URL)}`, '_blank');
        }
    }, [imageBlob]);

    const handleInstagram = useCallback(async () => {
        // Instagram has no web share-to-story API.
        // Mobile: native share sheet lets the user pick Instagram.
        // Desktop: download + show guidance.
        const shared = await nativeShare(imageBlob, 'instagram');
        if (!shared) {
            // Already downloaded via nativeShare fallback
            window.open('https://www.instagram.com/', '_blank');
        }
    }, [imageBlob]);

    const handleFacebook = useCallback(async () => {
        // For Facebook Stories: native share on mobile; web share URL on desktop.
        const shared = await nativeShare(imageBlob, 'facebook');
        if (!shared) {
            window.open(
                `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(SITE_URL)}&quote=${encodeURIComponent(SHARE_TEXT)}`,
                '_blank'
            );
        }
    }, [imageBlob]);

    const handleX = useCallback(() => {
        window.open(
            `https://twitter.com/intent/tweet?text=${encodeURIComponent(SHARE_TEXT)}&url=${encodeURIComponent(SITE_URL)}`,
            '_blank'
        );
    }, []);

    return (
        <div className="share-modal-backdrop" onClick={onClose}>
            <div
                className="share-modal-panel"
                onClick={(e) => e.stopPropagation()}
                role="dialog"
                aria-modal="true"
                aria-label="Share your recommendations"
            >
                {/* Close button */}
                <button className="share-modal-close" onClick={onClose} aria-label="Close">
                    <X size={20} strokeWidth={2.5} />
                </button>

                {/* Title */}
                <div className="share-modal-header">
                    <h3 className="share-modal-title">Share Your Recommendations</h3>
                    <p className="share-modal-subtitle">
                        Share your AI-generated university path with friends and inspire them!
                    </p>
                </div>

                {/* Image Preview */}
                {imageUrl && (
                    <div className="share-modal-preview-wrap">
                        <img
                            src={imageUrl}
                            alt="Your recommendations share card"
                            className="share-modal-preview"
                        />
                    </div>
                )}

                {/* Platform Buttons */}
                <div className="share-modal-platforms">
                    {/* WhatsApp */}
                    <button
                        className="platform-btn whatsapp-btn"
                        onClick={handleWhatsApp}
                        title="Share to WhatsApp Status"
                    >
                        <WhatsAppIcon />
                        <span>WhatsApp</span>
                    </button>

                    {/* Instagram */}
                    <button
                        className="platform-btn instagram-btn"
                        onClick={handleInstagram}
                        title="Share to Instagram Story"
                    >
                        <InstagramIcon />
                        <span>Instagram</span>
                    </button>

                    {/* Facebook */}
                    <button
                        className="platform-btn facebook-btn"
                        onClick={handleFacebook}
                        title="Share to Facebook Story"
                    >
                        <FacebookIcon />
                        <span>Facebook</span>
                    </button>

                    {/* X / Twitter */}
                    <button
                        className="platform-btn x-btn"
                        onClick={handleX}
                        title="Share on X (Twitter)"
                    >
                        <XIcon />
                        <span>X</span>
                    </button>
                </div>

                {/* Download */}
                <button className="share-download-btn" onClick={handleDownload}>
                    <Download size={16} />
                    <span>Download Image</span>
                </button>

                <p className="share-modal-hint">
                    On mobile, tap a platform to share directly. On desktop, download the image first.
                </p>
            </div>
        </div>
    );
};

/* ── Inline SVG icons for social platforms ── */

const WhatsAppIcon = () => (
    <svg width="22" height="22" viewBox="0 0 32 32" fill="none">
        <circle cx="16" cy="16" r="16" fill="#25D366" />
        <path d="M22.9 9.1A9.7 9.7 0 0 0 16 6.3C10.7 6.3 6.4 10.6 6.4 15.9c0 1.7.4 3.3 1.2 4.7L6.3 25.7l5.2-1.4a9.8 9.8 0 0 0 4.5 1.1c5.3 0 9.6-4.3 9.6-9.6 0-2.6-1-5-2.7-6.7zm-6.9 14.8a8.1 8.1 0 0 1-4.1-1.1l-.3-.2-3.1.8.8-3-.2-.3a8.1 8.1 0 0 1-1.2-4.2c0-4.5 3.7-8.2 8.2-8.2 2.2 0 4.2.9 5.8 2.4a8.1 8.1 0 0 1 2.4 5.8c-.1 4.5-3.7 8-8.3 8zm4.5-6.1c-.2-.1-1.4-.7-1.6-.8-.2-.1-.4-.1-.5.1-.2.3-.6.8-.8 1-.1.2-.3.2-.5.1-.7-.3-1.4-.7-2-1.2-.5-.5-1-1.1-1.4-1.8-.1-.2 0-.4.1-.5.1-.1.2-.3.4-.5l.2-.3c.1-.1.1-.2.1-.4 0-.2-.5-1.2-.7-1.6-.2-.4-.4-.3-.5-.3h-.4c-.2 0-.4.1-.6.3-.2.2-.8.8-.8 2s.8 2.3 1 2.5c.1.1 1.7 2.6 4.2 3.6l.6.2c.9.4 1.8.3 2.4.2.7-.1 1.4-.6 1.6-1.2.2-.6.2-1.1.1-1.2-.1-.1-.3-.2-.5-.3z" fill="#fff" />
    </svg>
);

const InstagramIcon = () => (
    <svg width="22" height="22" viewBox="0 0 32 32" fill="none">
        <defs>
            <linearGradient id="ig-grad" x1="0" y1="32" x2="32" y2="0" gradientUnits="userSpaceOnUse">
                <stop stopColor="#f09433" />
                <stop offset="0.25" stopColor="#e6683c" />
                <stop offset="0.5" stopColor="#dc2743" />
                <stop offset="0.75" stopColor="#cc2366" />
                <stop offset="1" stopColor="#bc1888" />
            </linearGradient>
        </defs>
        <rect width="32" height="32" rx="8" fill="url(#ig-grad)" />
        <circle cx="16" cy="16" r="5.5" stroke="#fff" strokeWidth="2" fill="none" />
        <circle cx="22.5" cy="9.5" r="1.5" fill="#fff" />
        <rect x="6" y="6" width="20" height="20" rx="6" stroke="#fff" strokeWidth="2" fill="none" />
    </svg>
);

const FacebookIcon = () => (
    <svg width="22" height="22" viewBox="0 0 32 32" fill="none">
        <rect width="32" height="32" rx="6" fill="#1877F2" />
        <path d="M21 6h-3a5 5 0 0 0-5 5v3h-3v4h3v8h4v-8h3l1-4h-4v-3a1 1 0 0 1 1-1h3V6z" fill="#fff" />
    </svg>
);

const XIcon = () => (
    <svg width="22" height="22" viewBox="0 0 32 32" fill="none">
        <rect width="32" height="32" rx="6" fill="#000" />
        <path d="M18.24 14.3L25.6 6h-1.76L17.44 13.1 12.24 6H6l7.72 11.24L6 26h1.76l6.75-7.85L20.24 26H26.5L18.24 14.3zm-2.4 2.8-.78-1.12L8.38 7.3h2.68l5.02 7.18.78 1.12 6.52 9.34h-2.68l-4.86-6.84z" fill="#fff" />
    </svg>
);

export default ShareModal;
