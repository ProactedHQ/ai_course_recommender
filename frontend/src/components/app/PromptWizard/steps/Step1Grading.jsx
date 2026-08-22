import React, { useMemo, useState } from 'react';
import { Trash2, AlertCircle, HelpCircle } from 'lucide-react';
import { useSubjects } from '../../../../hooks/useSubjects.js';

const Step1Grading = ({ data, updateData, errors }) => {
    const { subjects, loading, error } = useSubjects();
    const grades = ['A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'D-', 'E'];
    const [showHelp, setShowHelp] = useState(false);

    const mathAltASelected = useMemo(() => {
        return data.subjects.some(sub => sub.name && sub.name.includes('Mathematics Alternative A'));
    }, [data.subjects]);

    const mathAltBSelected = useMemo(() => {
        return data.subjects.some(sub => sub.name && sub.name.includes('Mathematics Alternative B'));
    }, [data.subjects]);

    const availableSubjects = useMemo(() => {
        if (!subjects || subjects.length === 0) return [];

        return subjects.filter(subject => {
            const name = subject.name;
            if (name === 'Mathematics' || name === 'Mathematics (121)' || name === 'MATH') return false;
            if (mathAltASelected && name.includes('Mathematics Alternative B')) return false;
            if (mathAltBSelected && name.includes('Mathematics Alternative A')) return false;
            return true;
        });
    }, [subjects, mathAltASelected, mathAltBSelected]);

    const getCategoryFromName = (name) => {
        if (!name) return 0;
        const n = name.toLowerCase();
        if (n.includes('english') || n.includes('kiswahili') || n.includes('math')) return 1;
        if (n.includes('biology') || n.includes('physics') || n.includes('chemistry') || (n.includes('science') && !n.includes('home') && !n.includes('computer'))) return 2;
        if (n.includes('history') || n.includes('geography') || n.includes('religious') || n.includes('cre') || n.includes('ire') || n.includes('hre')) return 3;
        return 4;
    };

    const handleSubjectChange = (index, field, value) => {
        const newList = [...data.subjects];
        newList[index][field] = value;
        updateData({ subjects: newList });
    };

    const addSubject = (groupId) => {
        updateData({ subjects: [...data.subjects, { name: '', grade: '', _expectedGroup: groupId }] });
    };

    const removeSubject = (index) => {
        const newList = data.subjects.filter((_, i) => i !== index);
        updateData({ subjects: newList });
    };

    const getCategory = (sub) => {
        if (sub._expectedGroup) return sub._expectedGroup;
        return getCategoryFromName(sub.name);
    };

    const groupedSubjects = { 1: [], 2: [], 3: [], 4: [] };
    data.subjects.forEach((sub, index) => {
        const cat = getCategory(sub);
        if (cat !== 0) {
            groupedSubjects[cat].push({ ...sub, originalIndex: index });
        }
    });

    const groupTitles = {
        1: "Group I: Compulsory Subjects (All 3 mandatory)",
        2: "Group II: Sciences (Pick at least 2)",
        3: "Group III: Humanities (Pick at least 1)",
        4: "Group IV & V: Technical, Business & Languages"
    };

    const groupMaxLimits = {
        1: 3, 2: 4, 3: 5, 4: 15
    };

    const getAvailableForGroup = (groupId) => {
        return availableSubjects.filter(sub => getCategoryFromName(sub.name) === groupId);
    };

    const subjectCountError = errors?.['student_profile.kcse.subjects'];

    if (loading) {
        return <div className="wizard-step"><h2 className="step-title">KCSE Results (8-4-4)</h2><p className="step-description">Loading subjects...</p></div>;
    }

    if (error) {
        return <div className="wizard-step"><div className="step-level-error"><AlertCircle size={14} /> Error loading subjects: {error}</div></div>;
    }

    return (
        <div className="wizard-step">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <h2 className="step-title" style={{ marginBottom: 0 }}>KCSE Results (8-4-4) <span className="required-asterisk">*</span></h2>
                <button type="button" onClick={() => setShowHelp(!showHelp)} style={{ background: 'none', border: 'none', color: 'var(--color-info)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '5px', fontWeight: '800', fontSize: '0.9rem' }}>
                    <HelpCircle size={18} /> {showHelp ? 'Hide Rules' : 'KUCCPS Rules'}
                </button>
            </div>
            
            <p className="step-description" style={{ marginBottom: showHelp ? '1rem' : '2rem' }}>
                Add your subjects into the correct categories below.
            </p>

            {showHelp && (
                <div style={{ backgroundColor: 'var(--color-info-bg)', padding: '1rem', borderLeft: '4px solid var(--color-info)', marginBottom: '2rem', fontSize: '0.85rem', color: 'var(--color-info)' }}>
                    <h4 style={{ marginTop: 0, marginBottom: '0.5rem', color: 'var(--color-info)', fontSize: '1rem' }}>KUCCPS Subject Grouping:</h4>
                    <p style={{ margin: '0 0 4px 0', color: 'var(--color-info)' }}><strong>Group I (Compulsory):</strong> English, Kiswahili, Math.</p>
                    <p style={{ margin: '0 0 4px 0', color: 'var(--color-info)' }}><strong>Group II (Sciences):</strong> Biology, Physics, Chemistry, General Science. <em>(Min 2 required)</em></p>
                    <p style={{ margin: '0 0 4px 0', color: 'var(--color-info)' }}><strong>Group III (Humanities):</strong> History, Geography, CRE/IRE/HRE. <em>(Min 1 required)</em></p>
                    <p style={{ margin: 0, color: 'var(--color-info)' }}><strong>Group IV & V:</strong> Applied Sciences, Business, Languages. <em>(Used to reach 7 subjects min)</em></p>
                </div>
            )}

            {subjectCountError && (
                <div className="step-level-error">
                    <AlertCircle size={14} />
                    {subjectCountError}
                </div>
            )}

            <div className="subjects-grid" style={{ gap: '1.5rem' }}>
                {[1, 2, 3, 4].map(groupId => {
                    const groupItems = groupedSubjects[groupId];
                    const maxAllowed = groupMaxLimits[groupId];
                    const groupOptions = getAvailableForGroup(groupId);

                    return (
                        <div key={`group-${groupId}`} style={{ border: '1px solid var(--color-border)', padding: '1rem', background: 'var(--color-bg-card)' }}>
                            <h4 className="group-category-title" style={{ fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '1rem', borderBottom: '1px solid var(--color-border)', paddingBottom: '0.5rem', fontWeight: '800' }}>
                                {groupTitles[groupId]}
                            </h4>
                            
                            {groupItems.length === 0 ? (
                                <div style={{ fontSize: '0.8rem', fontStyle: 'italic', color: 'var(--color-text-muted)', paddingBottom: '0.5rem' }}>
                                    No subjects added to this category yet.
                                </div>
                            ) : (
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                                    {groupItems.map(item => {
                                        const index = item.originalIndex;
                                        const gradeError = errors?.[`student_profile.kcse.subjects.${index}.grade`];
                                        const nameError = errors?.[`student_profile.kcse.subjects.${index}.name`];

                                        return (
                                            <div key={`sub-${index}`} className="subject-row-wrapper">
                                                <div className="subject-row">
                                                    <select
                                                        value={item.name}
                                                        onChange={(e) => handleSubjectChange(index, 'name', e.target.value)}
                                                        className={`form-select ${nameError ? 'input-error' : ''}`}
                                                    >
                                                        <option value="">Select Subject</option>
                                                        {groupOptions.map(s => (
                                                            <option key={s.id} value={s.name}>{s.name}</option>
                                                        ))}
                                                    </select>
                                                    <select
                                                        value={item.grade}
                                                        onChange={(e) => handleSubjectChange(index, 'grade', e.target.value)}
                                                        className={`form-select ${gradeError ? 'input-error' : ''}`}
                                                    >
                                                        <option value="">Grade</option>
                                                        {grades.map(g => <option key={g} value={g}>{g}</option>)}
                                                    </select>
                                                    <button className="btn-remove-premium" onClick={() => removeSubject(index)}>
                                                        <Trash2 size={18} />
                                                    </button>
                                                </div>
                                                {(gradeError || nameError) && (
                                                    <div className="field-error-text" style={{ marginTop: '0.2rem' }}>
                                                        {nameError || gradeError}
                                                    </div>
                                                )}
                                            </div>
                                        );
                                    })}
                                </div>
                            )}

                            {groupItems.length < maxAllowed && (
                                <button className="btn-add secondary" style={{ marginTop: '1rem', fontSize: '0.8rem', padding: '0.5rem 1rem' }} onClick={() => addSubject(groupId)}>
                                    + Add Subject
                                </button>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default Step1Grading;

