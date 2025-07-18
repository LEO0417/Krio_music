import React, { useCallback } from 'react';
import styled from 'styled-components';

export interface SliderProps {
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
  disabled?: boolean;
  label?: string;
  showValue?: boolean;
  formatValue?: (value: number) => string;
}

const SliderWrapper = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
`;

const SliderHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const Label = styled.label`
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
`;

const Value = styled.span`
  font-size: 14px;
  color: var(--color-text-secondary);
  font-weight: 500;
`;

const SliderTrack = styled.div`
  position: relative;
  height: 6px;
  background: var(--color-background-secondary);
  border-radius: 3px;
  cursor: pointer;
`;

const SliderFill = styled.div<{ percentage: number }>`
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  background: linear-gradient(90deg, #007aff 0%, #0056b3 100%);
  border-radius: 3px;
  width: ${props => props.percentage}%;
  transition: width 0.1s ease;
`;

const SliderThumb = styled.div<{ percentage: number; isDragging?: boolean }>`
  position: absolute;
  top: 50%;
  left: ${props => props.percentage}%;
  width: 20px;
  height: 20px;
  background: white;
  border: 2px solid #007aff;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  
  ${props => props.isDragging && `
    transform: translate(-50%, -50%) scale(1.2);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
  `}
  
  &:hover {
    transform: translate(-50%, -50%) scale(1.1);
  }
`;

const HiddenInput = styled.input`
  position: absolute;
  opacity: 0;
  pointer-events: none;
`;

export const Slider: React.FC<SliderProps> = ({
  value,
  onChange,
  min = 0,
  max = 100,
  step = 1,
  disabled = false,
  label,
  showValue = true,
  formatValue,
}) => {
  const percentage = ((value - min) / (max - min)) * 100;
  const displayValue = formatValue ? formatValue(value) : value.toString();

  const handleTrackClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (disabled) return;
      
      const rect = e.currentTarget.getBoundingClientRect();
      const clickX = e.clientX - rect.left;
      const trackWidth = rect.width;
      const newPercentage = (clickX / trackWidth) * 100;
      const newValue = min + (newPercentage / 100) * (max - min);
      
      // Round to nearest step
      const steppedValue = Math.round(newValue / step) * step;
      const clampedValue = Math.max(min, Math.min(max, steppedValue));
      
      onChange(clampedValue);
    },
    [disabled, min, max, step, onChange]
  );

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (disabled) return;
      onChange(Number(e.target.value));
    },
    [disabled, onChange]
  );

  return (
    <SliderWrapper>
      {(label || showValue) && (
        <SliderHeader>
          {label && <Label>{label}</Label>}
          {showValue && <Value>{displayValue}</Value>}
        </SliderHeader>
      )}
      
      <SliderTrack onClick={handleTrackClick}>
        <SliderFill percentage={percentage} />
        <SliderThumb percentage={percentage} />
      </SliderTrack>
      
      <HiddenInput
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={handleInputChange}
        disabled={disabled}
      />
    </SliderWrapper>
  );
};