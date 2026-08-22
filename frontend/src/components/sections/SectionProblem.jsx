import { Library, Compass, TrendingDown } from "lucide-react";
import "./SectionProblem.css";

const SectionProblem = () => {
    const problems = [
        {
            title: "Overwhelming Choices",
            description: "Thousands of courses and institutions make it hard to decide confidently.",
            icon: <Library size={24} />
        },
        {
            title: "Lack of Personalized Guidance",
            description: "Generic advice ignores your strengths, interests, and cluster requirements.",
            icon: <Compass size={24} />
        },
        {
            title: "Mismatch with Market Needs",
            description: "Students may choose courses without understanding real career prospects.",
            icon: <TrendingDown size={24} />
        }
    ];


    return (
        <section className="section-outer problem-section" id="problem">
            <div className="section-inner">
                <h2 className="section-title">Why Choosing the Right Course Is Hard</h2>
                <div className="problem-grid">
                    {problems.map((problem, index) => (
                        <div key={index} className="problem-card">
                            <div className="problem-icon">{problem.icon}</div>
                            <h3 className="problem-card-title">{problem.title}</h3>
                            <p className="problem-card-description">{problem.description}</p>
                        </div>

                    ))}
                </div>
            </div>
        </section>
    );
};

export default SectionProblem;
