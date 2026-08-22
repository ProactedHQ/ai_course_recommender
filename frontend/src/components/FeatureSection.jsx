import './FeatureSection.css';

const FeatureSection = ({ image, title, description, flipped }) => {
    return (
        <section className={`feature-section ${flipped ? 'flipped' : ''}`}>
            <div className="feature-container">
                <div className="feature-content">
                    {title && <h2 className="feature-title">{title}</h2>}
                    {description && <p className="feature-description">{description}</p>}
                </div>
                <div className="feature-image-wrapper">
                    <img src={image} alt={title || "Feature demonstration"} className="feature-image" />
                </div>
            </div>
        </section>
    );
};

export default FeatureSection;
