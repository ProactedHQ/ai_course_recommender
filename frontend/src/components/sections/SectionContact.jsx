import { useState } from "react";
import { Mail, MapPin, MessageSquare } from "lucide-react";
import WhatsAppConsentModal from "../common/WhatsAppConsentModal";
import "./SectionContact.css";

const SectionContact = () => {
    const [isModalOpen, setIsModalOpen] = useState(false);

    return (
        <section className="section-outer contact-section" id="get-in-touch">
            <div className="section-inner contact-container">
                <div className="contact-info">
                    <h2 className="section-title" style={{ textAlign: 'left', marginBottom: '30px' }}>Get in Touch</h2>
                    <p className="contact-description">
                        Have questions about KeDira? Our team is here to help you navigate your educational journey.
                    </p>
                    <div className="contact-details">
                        <div className="contact-item">
                            <span className="icon-premium"><Mail size={20} /></span>
                            <div>
                                <strong>Email</strong>
                                <p>support@proactedai.co.ke</p>
                            </div>
                        </div>
                        <div className="contact-item">
                            <span className="icon-premium"><MapPin size={20} /></span>
                            <div>
                                <strong>Location</strong>
                                <p>Kisumu, Kenya</p>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="contact-cta-box">
                    <div className="cta-glass-overlay"></div>
                    <div className="cta-glow-emitter"></div>

                    <div className="cta-content-wrapper">
                        <div className="cta-icon-wrapper">
                            <MessageSquare size={42} className="cta-icon-main" strokeWidth={1.5} />
                        </div>
                        <h3>Need Help Choosing?</h3>
                        <p>Our student support team is ready to help you plan your career path via WhatsApp.</p>

                        <button
                            className="btn-whatsapp-cta-premium"
                            onClick={() => setIsModalOpen(true)}
                            style={{
                                border: 'none',
                                cursor: 'pointer',
                                font: 'inherit',
                                display: 'inline-flex',
                                alignItems: 'center',
                                justifyContent: 'center'
                            }}
                        >
                            <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor" style={{ marginRight: '12px' }}>
                                <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.414 0 .004 5.412.001 12.048a11.82 11.82 0 001.576 5.905L0 24l6.117-1.605a11.845 11.845 0 005.933 1.598h.005c6.637 0 12.048-5.412 12.05-12.049a11.83 11.83 0 00-3.41-8.461z" />
                            </svg>
                            Start WhatsApp Chat
                        </button>
                        <WhatsAppConsentModal
                            isOpen={isModalOpen}
                            onClose={() => setIsModalOpen(false)}
                        />
                    </div>
                </div>
            </div>
        </section>
    );
};

export default SectionContact;
