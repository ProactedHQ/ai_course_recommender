import React, { useState, useEffect } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import Navbar from "../../components/Navbar";
import Footer from "../../components/Footer";
import { ArrowLeft, Calendar, Clock, Tag, User, ArrowRight, Twitter, Linkedin, Facebook, Share2, MessageCircle, Heart, Eye, Users } from "lucide-react";
import blogPosts from "./blogData";
import blogApi from "../../api/blogApi";
import { useAuth } from "../../context/AuthContext";
import "./BlogPost.css";

const BlogPost = () => {
    const { slug } = useParams();
    const navigate = useNavigate();
    const { user } = useAuth();
    const post = blogPosts.find((p) => p.slug === slug);

    const [stats, setStats] = useState({
        likes_count: 0,
        views_count: 0,
        is_liked_by_user: false,
        viewers: [],
        likers: []
    });
    const [loadingStats, setLoadingStats] = useState(true);

    useEffect(() => {
        if (post) {
            fetchStats();
            recordView();
        }
    }, [slug]);

    const fetchStats = async () => {
        try {
            const response = await blogApi.getStats(slug);
            setStats(response.data);
        } catch (error) {
            console.error("Error fetching blog stats:", error);
        } finally {
            setLoadingStats(false);
        }
    };

    const recordView = async () => {
        try {
            await blogApi.recordView(slug);
        } catch (error) {
            console.error("Error recording view:", error);
        }
    };

    const handleLike = async () => {
        try {
            const response = await blogApi.toggleLike(slug);
            // Optimistic update
            setStats(prev => ({
                ...prev,
                is_liked_by_user: !prev.is_liked_by_user,
                likes_count: response.data.status === 'liked' ? prev.likes_count + 1 : prev.likes_count - 1
            }));
        } catch (error) {
            console.error("Error toggling like:", error);
        }
    };

    if (!post) {
        return (
            <div className="blog-post-page">
                <Navbar />
                <div className="section-outer blog-post-not-found">
                    <div className="section-inner">
                        <h2>Post Not Found</h2>
                        <p>The blog post you're looking for doesn't exist.</p>
                        <Link to="/kedira-insider" className="back-to-blog">
                            <ArrowLeft size={18} />
                            Back to Blog
                        </Link>
                    </div>
                </div>
                <Footer />
            </div>
        );
    }

    const formatDate = (dateStr) => {
        const date = new Date(dateStr);
        return date.toLocaleDateString("en-KE", {
            year: "numeric",
            month: "long",
            day: "numeric",
        });
    };

    const handleShare = async (platform) => {
        const url = window.location.href;
        const text = `Check out this article from KeDira: ${post.title}`;

        if (platform === 'twitter') {
            window.open(`https://twitter.com/intent/tweet?url=${encodeURIComponent(url)}&text=${encodeURIComponent(text)}`, '_blank');
        } else if (platform === 'linkedin') {
            window.open(`https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}`, '_blank');
        } else if (platform === 'facebook') {
            window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`, '_blank');
        } else if (platform === 'whatsapp') {
            window.open(`https://api.whatsapp.com/send?text=${encodeURIComponent(text + " " + url)}`, '_blank');
        } else if (platform === 'native') {
            if (navigator.share) {
                try {
                    await navigator.share({ title: post.title, text: text, url: url });
                } catch (error) {
                    console.error('Error sharing', error);
                }
            } else {
                navigator.clipboard.writeText(url);
                alert("Link copied to clipboard!");
            }
        }
    };

    const renderContentBlock = (block, index) => {
        switch (block.type) {
            case "introduction":
                return (
                    <div key={index} className="content-introduction">
                        <p>{block.value}</p>
                    </div>
                );

            case "heading":
                return (
                    <h2 key={index} className="content-heading">
                        {block.value}
                    </h2>
                );

            case "paragraph":
                return (
                    <p key={index} className="content-paragraph">
                        {block.value}
                    </p>
                );

            case "list":
                return (
                    <ul key={index} className="content-list">
                        {block.value.map((item, i) => {
                            const colonIndex = item.indexOf(":");
                            if (colonIndex > 0 && colonIndex < 50) {
                                return (
                                    <li key={i}>
                                        <strong>{item.substring(0, colonIndex + 1)}</strong>
                                        {item.substring(colonIndex + 1)}
                                    </li>
                                );
                            }
                            return <li key={i}>{item}</li>;
                        })}
                    </ul>
                );

            case "blockquote":
                return (
                    <blockquote key={index} className="content-blockquote">
                        <p>{block.value}</p>
                    </blockquote>
                );

            case "conclusion":
                return (
                    <div key={index} className="content-conclusion">
                        <p>{block.value}</p>
                    </div>
                );

            case "cta":
                return (
                    <div key={index} className="content-cta">
                        <div className="cta-inner">
                            <p>{block.value}</p>
                            <Link to="/signup" className="cta-button">
                                Get Started Free
                                <ArrowRight size={18} />
                            </Link>
                        </div>
                    </div>
                );

            default:
                return (
                    <p key={index} className="content-paragraph">
                        {block.value}
                    </p>
                );
        }
    };

    return (
        <div className="blog-post-page">
            <Navbar />
            <article className="section-outer blog-post-section">
                <div className="section-inner">
                    <Link to="/kedira-insider" className="back-to-blog">
                        <ArrowLeft size={18} />
                        Back to Blog
                    </Link>

                    <header className="post-header">
                        <span className="post-category-badge">{post.category}</span>
                        <h1 className="post-title">{post.title}</h1>
                        <div className="post-meta">
                            <span className="meta-item">
                                <User size={16} />
                                {post.author}
                            </span>
                            <span className="meta-divider">·</span>
                            <span className="meta-item">
                                <Calendar size={16} />
                                {formatDate(post.date)}
                            </span>
                            <span className="meta-divider">·</span>
                            <span className="meta-item">
                                <Clock size={16} />
                                {post.readTime}
                            </span>
                            <span className="meta-divider">·</span>
                            <span className="meta-item stats-item">
                                <Eye size={16} />
                                {stats.views_count} views
                            </span>
                        </div>
                    </header>

                    {post.thumbnail && (
                        <div className="post-thumbnail">
                            <img src={post.thumbnail} alt={post.title} />
                        </div>
                    )}

                    <div className="post-body">
                        {post.content.map((block, index) => renderContentBlock(block, index))}
                    </div>

                    <div className="interaction-section">
                        <div className="interaction-buttons">
                            <button
                                onClick={handleLike}
                                className={`like-button ${stats.is_liked_by_user ? 'liked' : ''}`}
                                aria-label="Like this post"
                            >
                                <Heart size={24} fill={stats.is_liked_by_user ? "currentColor" : "none"} />
                                <span>{stats.likes_count} Likes</span>
                            </button>
                        </div>

                        {stats.viewers.length > 0 && (
                            <div className="viewers-list-section">
                                <div className="viewers-header">
                                    <Users size={18} />
                                    <h4>Individuals who have viewed this article:</h4>
                                </div>
                                <div className="viewers-grid">
                                    {stats.viewers.map((viewer) => (
                                        <div key={viewer.id} className="viewer-chip">
                                            <div className="viewer-avatar">
                                                {viewer.first_name ? viewer.first_name[0] : viewer.username[0]}
                                            </div>
                                            <span>
                                                {viewer.first_name && viewer.last_name
                                                    ? `${viewer.first_name} ${viewer.last_name}`
                                                    : viewer.username}
                                            </span>
                                        </div>
                                    ))}
                                    {stats.viewers.length > 5 && (
                                        <div className="viewer-more">
                                            +{stats.viewers.length - 5} more
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>

                    <div className="share-section">
                        <h3>Share this article</h3>
                        <div className="share-buttons">
                            <button onClick={() => handleShare('whatsapp')} className="share-btn whatsapp" aria-label="Share on WhatsApp">
                                <MessageCircle size={18} />
                                <span>WhatsApp</span>
                            </button>
                            <button onClick={() => handleShare('twitter')} className="share-btn twitter" aria-label="Share on X (Twitter)">
                                <Twitter size={18} />
                                <span>X (Twitter)</span>
                            </button>
                            <button onClick={() => handleShare('linkedin')} className="share-btn linkedin" aria-label="Share on LinkedIn">
                                <Linkedin size={18} />
                                <span>LinkedIn</span>
                            </button>
                            <button onClick={() => handleShare('facebook')} className="share-btn facebook" aria-label="Share on Facebook">
                                <Facebook size={18} />
                                <span>Facebook</span>
                            </button>
                            <button onClick={() => handleShare('native')} className="share-btn native" aria-label="Share Link">
                                <Share2 size={18} />
                                <span>Share Link</span>
                            </button>
                        </div>
                    </div>
                </div>
            </article>
            <Footer />
        </div>
    );
};

export default BlogPost;
