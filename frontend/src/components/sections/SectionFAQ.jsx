import { useState } from "react";
import { HelpCircle, ChevronDown } from "lucide-react";
import "./SectionFAQ.css";

const SectionFAQ = () => {
    const [activeIndex, setActiveIndex] = useState(null);

    const faqs = [
        {
            question: "How does the AI matching work?",
            answer: "Our system uses advanced algorithms to compare your KCSE results and interests against the latest KUCCPS cluster requirements and market demand data."
        },
        {
            question: "Is KeDira officially affiliated with KUCCPS?",
            answer: "We are an independent guidance platform that uses publicly available KUCCPS guidelines to help students make informed decisions."
        },
        {
            question: "Can I use the Free tier forever?",
            answer: "Yes! You can use the free tier for basic recommendations. You only need to upgrade if you want unlimited prompts and deep career analysis."
        },
        {
            question: "What if I haven't received my KCSE results yet?",
            answer: "You can input your mock results or expected grades to get a preliminary idea of what you might qualify for."
        },
        {
            question: "How do I upgrade to Premium?",
            answer: "Simply click 'Go Premium' on the pricing page. We support secure mobile money and card payments."
        }
    ];

    const toggleFAQ = (index) => {
        setActiveIndex(activeIndex === index ? null : index);
    };

    return (
        <section className="section-outer faq-section" id="faq">
            <div className="section-inner">
                <h2 className="section-title">Frequently Asked Questions</h2>
                <div className="faq-container">
                    {faqs.map((faq, index) => (
                        <div key={index} className={`faq-item ${activeIndex === index ? "active" : ""}`}>
                            <button className="faq-question" onClick={() => toggleFAQ(index)}>
                                <div className="question-text-wrapper">
                                    <HelpCircle size={24} className="faq-icon" />
                                    <span>{faq.question}</span>
                                </div>
                                <ChevronDown size={20} className={`faq-chevron ${activeIndex === index ? "rotated" : ""}`} />
                            </button>
                            <div className="faq-answer">
                                <p>{faq.answer}</p>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
};


export default SectionFAQ;
