import React, { useMemo } from 'react';
import { useSubjects } from '../../../hooks/useSubjects';

const Step1Academic = ({ data, updateData }) => {
    const { subjects, loading, error } = useSubjects();
    const grades = ['A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'D-', 'E'];

    // Check which Math alternative is selected
    const mathAltASelected = useMemo(() => {
        return Object.entries(data.kcseGrades || {}).some(([subjectName, grade]) =>
            subjectName.includes('Mathematics Alternative A') && grade
        );
    }, [data.kcseGrades]);

    const mathAltBSelected = useMemo(() => {
        return Object.entries(data.kcseGrades || {}).some(([subjectName, grade]) =>
            subjectName.includes('Mathematics Alternative B') && grade
        );
    }, [data.kcseGrades]);

    // Filter subjects based on Math Alt selection
    const availableSubjects = useMemo(() => {
        if (!subjects || subjects.length === 0) return [];

        return subjects.filter(subject => {
            // If Math Alt A is selected, hide Math Alt B
            if (mathAltASelected && subject.name.includes('Mathematics Alternative B')) {
                return false;
            }
            // If Math Alt B is selected, hide Math Alt A
            if (mathAltBSelected && subject.name.includes('Mathematics Alternative A')) {
                return false;
            }
            return true;
        });
    }, [subjects, mathAltASelected, mathAltBSelected]);

    const handleGradeChange = (subjectName, grade) => {
        updateData({
            kcseGrades: { ...data.kcseGrades, [subjectName]: grade }
        });
    };

    if (loading) {
        return (
            <div className="step-content">
                <h2 className="step-label">Academic Results</h2>
                <p className="step-description">Loading subjects...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="step-content">
                <h2 className="step-label">Academic Results</h2>
                <p className="step-description" style={{ color: '#e53e3e' }}>
                    Error loading subjects: {error}. Please refresh the page.
                </p>
            </div>
        );
    }

    return (
        <div className="step-content">
            <h2 className="step-label">Academic Results</h2>
            <p className="step-description">Enter your KCSE grades to help us calculate your cluster points.</p>

            <div className="form-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginTop: '2rem' }}>
                <div className="form-field full-width" style={{ gridColumn: 'span 2' }}>
                    <label>Mean Grade</label>
                    <select
                        value={data.meanGrade || ''}
                        onChange={(e) => updateData({ meanGrade: e.target.value })}
                        style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', border: '1px solid #e2e8f0' }}
                    >
                        <option value="">Select Mean Grade</option>
                        {grades.map(g => <option key={g} value={g}>{g}</option>)}
                    </select>
                </div>

                {availableSubjects.map(subject => (
                    <div className="form-field" key={subject.id}>
                        <label>{subject.name}</label>
                        <select
                            value={data.kcseGrades?.[subject.name] || ''}
                            onChange={(e) => handleGradeChange(subject.name, e.target.value)}
                            style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', border: '1px solid #e2e8f0' }}
                        >
                            <option value="">Grade</option>
                            {grades.map(g => <option key={g} value={g}>{g}</option>)}
                        </select>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default Step1Academic;

