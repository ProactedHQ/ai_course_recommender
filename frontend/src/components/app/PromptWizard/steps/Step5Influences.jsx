import React from 'react';
import { Trash2, AlertCircle } from 'lucide-react';
import FieldHelp from '../FieldHelp.jsx';

const Step5Influences = ({ data, updateData, errors }) => {
    const influencerTypes = ["parent", "sibling", "relative", "friend", "teacher", "mentor", "role_model", "other"];
    const paths = ["university", "tvet", "employment", "business"];
    const strengths = [1, 2, 3, 4];
    const reasons = ["advice", "example", "pressure", "support"];
    const alignments = ["agree", "partially_agree", "neutral", "disagree_but_complying"];

    const addInfluencer = () => {
        const newInfluencer = {
            influencer_type: "parent",
            direction_field: "",
            general_path: "university",
            strength: 3,
            reason: "advice",
            student_alignment: "neutral",
            notes: ""
        };
        updateData([...data, newInfluencer]);
    };

    const removeInfluencer = (index) => {
        updateData(data.filter((_, i) => i !== index));
    };

    const handleChange = (index, field, value) => {
        const newList = [...data];
        newList[index][field] = value;
        updateData(newList);
    };

    const influencerError = errors?.['student_profile.influences'];

    return (
        <div className="wizard-step">
            <h2 className="step-title">
                Influences <span className="required-asterisk">*</span>
                <FieldHelp 
                    title="Influences" 
                    content={<><strong>💡 What to enter:</strong> Is a parent, teacher, or friend pushing you towards a specific career (e.g., Nursing or Engineering)? How strongly do you agree with them?<br/><br/><strong>Why it matters:</strong> We understand there can be pressure from family. The AI considers these external influences and tries to find a 'middle-ground' recommendation that satisfies both your sponsors' wishes and your own passions.</>} 
                />
            </h2>
            <p className="step-description">Who is guiding your decisions, and what path are they suggesting?</p>

            {influencerError && (
                <div className="step-level-error">
                    <AlertCircle size={14} />
                    {influencerError}
                </div>
            )}

            <div className="influences-list">
                {data.map((inf, index) => (
                    <div key={index} className="influence-card">
                        <div className="card-header">
                            <span className="card-title">Influencer #{index + 1}</span>
                            <button className="btn-remove-sm" onClick={() => removeInfluencer(index)}>
                                <Trash2 size={14} />
                                Remove
                            </button>
                        </div>

                        <div className="form-grid-3">
                            <div className="form-section">
                                <label className="form-label-sm">Type</label>
                                <select
                                    className="form-select-sm"
                                    value={inf.influencer_type}
                                    onChange={(e) => handleChange(index, 'influencer_type', e.target.value)}
                                >
                                    {influencerTypes.map(t => <option key={t} value={t}>{t}</option>)}
                                </select>
                            </div>
                            <div className="form-section">
                                <label className="form-label-sm">Advised Field</label>
                                <input
                                    type="text"
                                    className="form-input-sm"
                                    placeholder="e.g. Medicine"
                                    value={inf.direction_field}
                                    onChange={(e) => handleChange(index, 'direction_field', e.target.value)}
                                />
                            </div>
                            <div className="form-section">
                                <label className="form-label-sm">Path</label>
                                <select
                                    className="form-select-sm"
                                    value={inf.general_path}
                                    onChange={(e) => handleChange(index, 'general_path', e.target.value)}
                                >
                                    {paths.map(p => <option key={p} value={p}>{p}</option>)}
                                </select>
                            </div>
                        </div>

                        <div className="form-grid-3">
                            <div className="form-section">
                                <label className="form-label-sm">Strength</label>
                                <select
                                    className="form-select-sm"
                                    value={inf.strength}
                                    onChange={(e) => handleChange(index, 'strength', parseInt(e.target.value))}
                                >
                                    {strengths.map(s => <option key={s} value={s}>{s} {s === 1 ? '(Weak)' : s === 4 ? '(Strong)' : ''}</option>)}
                                </select>
                            </div>
                            <div className="form-section">
                                <label className="form-label-sm">Reason</label>
                                <select
                                    className="form-select-sm"
                                    value={inf.reason}
                                    onChange={(e) => handleChange(index, 'reason', e.target.value)}
                                >
                                    {reasons.map(r => <option key={r} value={r}>{r}</option>)}
                                </select>
                            </div>
                            <div className="form-section">
                                <label className="form-label-sm">Your Alignment</label>
                                <select
                                    className="form-select-sm"
                                    value={inf.student_alignment}
                                    onChange={(e) => handleChange(index, 'student_alignment', e.target.value)}
                                >
                                    {alignments.map(a => <option key={a} value={a}>{a.replace('_', ' ')}</option>)}
                                </select>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            <button className="btn-add dashed" onClick={addInfluencer}>+ Add Influencer</button>
        </div>
    );
};

export default Step5Influences;
