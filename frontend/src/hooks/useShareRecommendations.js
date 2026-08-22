import { useRef, useState, useCallback } from 'react';
import html2canvas from 'html2canvas';

/**
 * useShareRecommendations
 *
 * Encapsulates the logic for:
 *   1. Snapshotting the hidden <ShareCard> DOM node via html2canvas
 *   2. Converting it to a PNG blob / data URL
 *   3. Managing modal state
 *
 * @param {Array} recommendations — the top_5 array from PromptResult
 */
const useShareRecommendations = () => {
    const cardRef = useRef(null);
    const [isGenerating, setIsGenerating] = useState(false);
    const [imageBlob, setImageBlob] = useState(null);
    const [imageUrl, setImageUrl] = useState(null);
    const [showModal, setShowModal] = useState(false);
    const [error, setError] = useState(null);

    const handleShare = useCallback(async () => {
        if (!cardRef.current) return;
        setIsGenerating(true);
        setError(null);

        try {
            const canvas = await html2canvas(cardRef.current, {
                scale: 2,                 // 2× DPR → 1080 × 1920 output
                useCORS: true,            // allow favicon.png (same origin)
                backgroundColor: null,    // respect our CSS background
                logging: false,
                imageTimeout: 5000,
            });

            // Convert canvas to both Blob (for Web Share API) and Object URL (for <img> preview)
            canvas.toBlob((blob) => {
                if (!blob) {
                    setError('Failed to generate image. Please try again.');
                    setIsGenerating(false);
                    return;
                }
                // Revoke any previous object URL to avoid memory leaks
                if (imageUrl) URL.revokeObjectURL(imageUrl);

                const url = URL.createObjectURL(blob);
                setImageBlob(blob);
                setImageUrl(url);
                setIsGenerating(false);
                setShowModal(true);
            }, 'image/png');

        } catch (err) {
            console.error('[useShareRecommendations] html2canvas error:', err);
            setError('Could not generate share image. Please try again.');
            setIsGenerating(false);
        }
    }, [imageUrl]);

    const closeModal = useCallback(() => {
        setShowModal(false);
        // Do NOT revoke imageUrl here — user might re-open or download
    }, []);

    return {
        cardRef,
        handleShare,
        isGenerating,
        imageBlob,
        imageUrl,
        showModal,
        closeModal,
        error,
    };
};

export default useShareRecommendations;
