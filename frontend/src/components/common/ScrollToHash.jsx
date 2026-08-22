import { useEffect } from "react";
import { useLocation } from "react-router-dom";

const ScrollToHash = () => {
    const { hash, pathname } = useLocation();

    useEffect(() => {
        if (hash) {
            const id = hash.replace("#", "");
            const element = document.getElementById(id);
            if (element) {
                // Delay slightly to ensure content is rendered
                setTimeout(() => {
                    element.scrollIntoView({ behavior: "smooth" });
                }, 100);
            }
        } else {
            // Scroll to top on route change if no hash
            window.scrollTo(0, 0);
        }
    }, [hash, pathname]);

    return null;
};

export default ScrollToHash;
