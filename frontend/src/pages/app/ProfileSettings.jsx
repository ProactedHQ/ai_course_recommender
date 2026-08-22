import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import {
    User, Mail, Shield, UserCheck, Settings,
    BadgeCheck, Globe, CreditCard, Bell,
    Edit3, LogOut, Camera, Save, X
} from 'lucide-react';
import bannerImg from '../../assets/images/kenyan_student_hero.png';
import './ProfileSettings.css';

const ProfileSettings = () => {
    const { user, subscription, userProfile, updateProfile, signOut } = useAuth();
    const [isEditing, setIsEditing] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [formData, setFormData] = useState({
        fullName: '',
        bio: '',
        phoneNumber: ''
    });

    useEffect(() => {
        if (userProfile && !isEditing) {
            setFormData({
                fullName: `${userProfile.firstName} ${userProfile.lastName}`.trim() || user?.user_metadata?.full_name || '',
                bio: userProfile.bio || '',
                phoneNumber: userProfile.phoneNumber || ''
            });
        }
    }, [userProfile, user, isEditing]);

    const handleSave = async () => {
        try {
            setIsSaving(true);
            await updateProfile({
                phone_number: formData.phoneNumber,
                bio: formData.bio
            });
            setIsEditing(false);
        } catch (err) {
            console.error('Save failed:', err);
            alert('Failed to save profile. Please try again.');
        } finally {
            setIsSaving(false);
        }
    };

    const tierNames = {
        'explorer': 'Explorer Plan',
        'mentor_elite': 'Mentor Elite',
        'scholar_vvip': 'Scholar VVIP'
    };

    const tierDescriptions = {
        'explorer': 'You are on the basic plan with essential AI features.',
        'mentor_elite': 'You are on the Elite plan with professional career guidance.',
        'scholar_vvip': 'You are on the Scholar VVIP plan with full AI intelligence.'
    };

    const currentTierName = tierNames[subscription?.tier] || 'Explorer Plan';
    const currentTierDesc = tierDescriptions[subscription?.tier] || 'You are on the basic plan.';

    const initials = formData.fullName
        ? formData.fullName.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2)
        : 'AE';

    const email = user?.email;

    return (
        <div className="profile-settings-page-ultra">
            {/* Dynamic Interactive Banner */}
            <div className="ultra-banner-container" style={{ backgroundImage: `url(${bannerImg})` }}>
                <div className="ultra-banner-overlay"></div>
                <div className="ultra-banner-content">
                    <div className="profile-avatar-ultra-wrapper">
                        <div className="profile-avatar-ultra">
                            {initials}
                            <button className="camera-btn-ultra"><Camera size={16} /></button>
                        </div>
                        <div className="profile-status-ring"></div>
                    </div>
                    <div className="profile-hero-info">
                        <h1 className="hero-name">{formData.fullName || 'Academic Explorer'}</h1>
                        <div className="hero-badges">
                            <span className={`badge-pill ${subscription?.tier === 'explorer' ? '' : 'premium'}`}>
                                {currentTierName}
                            </span>
                            <span className="badge-pill location"><Globe size={12} /> Kenya</span>
                        </div>
                    </div>
                </div>
            </div>

            <div className="ultra-settings-full-wrapper">
                {/* Content Area with focused layout */}
                <main className="ultra-content-area">
                    <section className="ultra-card-glass main-info">
                        <div className="ultra-card-header">
                            <div className="header-icon-box cyan">
                                <UserCheck size={24} />
                            </div>
                            <div>
                                <h3>Identity Dashboard</h3>
                                <p>Manage how your academic profile appears to institutions.</p>
                            </div>
                            <div className="profile-actions-ultra">
                                {isEditing ? (
                                    <>
                                        <button
                                            className="save-btn-ultra"
                                            onClick={handleSave}
                                            disabled={isSaving}
                                        >
                                            {isSaving ? 'Saving...' : <><Save size={14} /> Save</>}
                                        </button>
                                        <button
                                            className="cancel-btn-ultra"
                                            onClick={() => setIsEditing(false)}
                                            disabled={isSaving}
                                        >
                                            <X size={14} /> Cancel
                                        </button>
                                    </>
                                ) : (
                                    <button className="edit-btn-ultra" onClick={() => setIsEditing(true)}>
                                        <Edit3 size={14} /> Edit
                                    </button>
                                )}
                            </div>
                        </div>

                        <div className="ultra-fields-grid">
                            <div className="ultra-field-group">
                                <label>Legal Full Name (Read-only)</label>
                                <div className="ultra-input-mock disabled">{formData.fullName || 'Not provided'}</div>
                            </div>
                            <div className="ultra-field-group">
                                <label>Phone Number</label>
                                {isEditing ? (
                                    <input
                                        type="text"
                                        className="ultra-input-real"
                                        value={formData.phoneNumber}
                                        onChange={(e) => setFormData({ ...formData, phoneNumber: e.target.value })}
                                        placeholder="e.g. 07XXXXXXXX"
                                    />
                                ) : (
                                    <div className="ultra-input-mock">{formData.phoneNumber || 'Not provided'}</div>
                                )}
                            </div>
                            <div className="ultra-field-group">
                                <label className="flex items-center gap-2">
                                    Verified Email <BadgeCheck size={14} className="verified-badge-pill" />
                                </label>
                                <div className="ultra-input-mock disabled">
                                    {email}
                                </div>
                            </div>
                            <div className="ultra-field-group"></div>
                            <div className="ultra-field-group full-width">
                                <label>Bio / Academic Aspirations (Max 500 chars)</label>
                                {isEditing ? (
                                    <textarea
                                        className="ultra-textarea-real"
                                        value={formData.bio}
                                        onChange={(e) => setFormData({ ...formData, bio: e.target.value.substring(0, 500) })}
                                        placeholder="Describe your goals and passion..."
                                        rows={4}
                                    />
                                ) : (
                                    <div className={`ultra-input-mock-long ${!formData.bio ? 'empty' : ''}`}>
                                        {formData.bio || 'No details provided yet. Click edit to share your goals.'}
                                    </div>
                                )}
                                {isEditing && (
                                    <span className="char-count-ultra">
                                        {formData.bio.length} / 500
                                    </span>
                                )}
                            </div>
                        </div>
                    </section>

                    <div className="ultra-cards-row">
                        <section className="ultra-card-glass flex-1">
                            <div className="ultra-card-header small">
                                <BadgeCheck size={20} className="text-amber-500" />
                                <h3>Membership</h3>
                            </div>
                            <p className="ultra-card-text">{currentTierDesc}</p>
                            <button className="ultra-btn-solid">Manage Plan</button>
                        </section>
                    </div>
                </main>
            </div>
        </div>
    );
};

export default ProfileSettings;
