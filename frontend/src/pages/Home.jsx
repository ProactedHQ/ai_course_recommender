import Navbar from '../components/Navbar';
import Hero from '../components/Hero';
import SectionProblem from '../components/sections/SectionProblem';
import SectionHowItWorks from '../components/sections/SectionHowItWorks';
import SectionFeatures from '../components/sections/SectionFeatures';
import SectionPricing from '../components/sections/SectionPricing';
import SectionFAQ from '../components/sections/SectionFAQ';
import SectionContact from '../components/sections/SectionContact';
import SectionCTA from '../components/sections/SectionCTA';
import Footer from '../components/Footer';

function Home() {
  return (
    <div className="home-page">
      <Navbar />
      <Hero />
      <SectionProblem />
      <SectionHowItWorks />
      <SectionFeatures />
      <SectionPricing />
      <SectionFAQ />
      <SectionContact />
      <SectionCTA />
      <Footer />
    </div>
  );
}

export default Home;
