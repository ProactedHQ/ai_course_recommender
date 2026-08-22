import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import Navbar from "../../components/Navbar";
import Footer from "../../components/Footer";
import { ArrowRight, Calendar, Clock, Heart, Eye } from "lucide-react";
import blogPosts from "./blogData";
import blogApi from "../../api/blogApi";
import "./BlogList.css";

const BlogCard = ({ post, formatDate }) => {
    const [stats, setStats] = useState({ likes_count: 0, views_count: 0 });

    useEffect(() => {
        const fetchCardStats = async () => {
            try {
                const response = await blogApi.getStats(post.slug);
                setStats({
                    likes_count: response.data.likes_count,
                    views_count: response.data.views_count
                });
            } catch (error) {
                console.error(`Error fetching stats for ${post.slug}:`, error);
            }
        };
        fetchCardStats();
    }, [post.slug]);

    return (
        <article className="blog-card">
            {post.thumbnail && (
                <Link to={`/kedira-insider/${post.slug}`} className="blog-card-image-link">
                    <img src={post.thumbnail} alt={post.title} className="blog-card-image" />
                </Link>
            )}
            <div className="blog-card-content">
                <div className="blog-card-meta">
                    <span className="blog-card-category">{post.category}</span>
                    <span className="blog-card-date">
                        <Calendar size={14} />
                        {formatDate(post.date)}
                    </span>
                    <span className="blog-card-time">
                        <Clock size={14} />
                        {post.readTime}
                    </span>
                </div>

                <Link to={`/kedira-insider/${post.slug}`} className="blog-card-title-link">
                    <h2 className="blog-card-title">{post.title}</h2>
                </Link>
                <p className="blog-card-excerpt">{post.excerpt}</p>

                <div className="blog-card-footer">
                    <Link to={`/kedira-insider/${post.slug}`} className="blog-card-read-more">
                        Read Article <ArrowRight size={16} />
                    </Link>
                    <div className="blog-card-stats">
                        <span className="stat-item">
                            <Heart size={14} fill={stats.likes_count > 0 ? "currentColor" : "none"} />
                            {stats.likes_count}
                        </span>
                        <span className="stat-item">
                            <Eye size={14} />
                            {stats.views_count}
                        </span>
                    </div>
                </div>
            </div>
        </article>
    );
};

const BlogList = () => {
    const formatDate = (dateStr) => {
        const date = new Date(dateStr);
        return date.toLocaleDateString("en-KE", {
            year: "numeric",
            month: "short",
            day: "numeric",
        });
    };

    return (
        <div className="blog-list-page">
            <Navbar />

            {/* Hero Section */}
            <section className="section-outer blog-hero-section">
                <div className="section-inner blog-hero-container">
                    <h1 className="blog-hero-title">KeDira Insider</h1>
                    <p className="blog-hero-subtitle">
                        Smart strategies, KUCCPS updates, and career advice for Kenyan students and families.
                    </p>
                </div>
            </section>

            {/* Blog Grid Section */}
            <section className="section-outer blog-grid-section">
                <div className="section-inner">
                    <div className="blog-grid">
                        {blogPosts.map((post) => (
                            <BlogCard key={post.id} post={post} formatDate={formatDate} />
                        ))}
                    </div>

                    {blogPosts.length === 0 && (
                        <div className="no-posts-message">
                            <p>Check back soon for new articles!</p>
                        </div>
                    )}
                </div>
            </section>

            <Footer />
        </div>
    );
};

export default BlogList;
