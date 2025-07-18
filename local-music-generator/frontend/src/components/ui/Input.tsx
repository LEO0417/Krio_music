import React from 'react';
import styled, { css } from 'styled-components';

export interface InputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
  error?: string;
  label?: string;
  type?: 'text' | 'email' | 'password' | 'number';
  fullWidth?: boolean;
  multiline?: boolean;
  rows?: number;
  maxLength?: number;
  autoFocus?: boolean;
}

const InputWrapper = styled.div<{ fullWidth?: boolean }>`
  display: flex;
  flex-direction: column;
  gap: 8px;
  ${props => props.fullWidth && css`width: 100%;`}
`;

const Label = styled.label`
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
`;

const InputBase = css`
  padding: 12px 16px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  font-size: 16px;
  font-family: inherit;
  background: var(--color-background-primary);
  color: var(--color-text-primary);
  transition: all 0.2s ease;
  
  &::placeholder {
    color: var(--color-text-secondary);
  }
  
  &:focus {
    outline: none;
    border-color: var(--color-primary);
    box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.1);
  }
  
  &:disabled {
    background: var(--color-background-disabled);
    color: var(--color-text-disabled);
    cursor: not-allowed;
  }
`;

const StyledInput = styled.input<{ hasError?: boolean; fullWidth?: boolean }>`
  ${InputBase}
  height: 44px;
  
  ${props => props.fullWidth && css`width: 100%;`}
  
  ${props => props.hasError && css`
    border-color: var(--color-danger);
    
    &:focus {
      border-color: var(--color-danger);
      box-shadow: 0 0 0 3px rgba(255, 59, 48, 0.1);
    }
  `}
`;

const StyledTextarea = styled.textarea<{ hasError?: boolean; fullWidth?: boolean }>`
  ${InputBase}
  min-height: 88px;
  resize: vertical;
  
  ${props => props.fullWidth && css`width: 100%;`}
  
  ${props => props.hasError && css`
    border-color: var(--color-danger);
    
    &:focus {
      border-color: var(--color-danger);
      box-shadow: 0 0 0 3px rgba(255, 59, 48, 0.1);
    }
  `}
`;

const ErrorMessage = styled.span`
  font-size: 12px;
  color: var(--color-danger);
  margin-top: 4px;
`;

const CharacterCount = styled.span`
  font-size: 12px;
  color: var(--color-text-secondary);
  text-align: right;
  margin-top: 4px;
`;

export const Input: React.FC<InputProps> = ({
  value,
  onChange,
  placeholder,
  disabled = false,
  error,
  label,
  type = 'text',
  fullWidth = false,
  multiline = false,
  rows = 4,
  maxLength,
  autoFocus = false,
}) => {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    onChange(e.target.value);
  };

  const InputComponent = multiline ? StyledTextarea : StyledInput;

  return (
    <InputWrapper fullWidth={fullWidth}>
      {label && <Label>{label}</Label>}
      <InputComponent
        value={value}
        onChange={handleChange}
        placeholder={placeholder}
        disabled={disabled}
        hasError={!!error}
        fullWidth={fullWidth}
        type={multiline ? undefined : type}
        rows={multiline ? rows : undefined}
        maxLength={maxLength}
        autoFocus={autoFocus}
      />
      {error && <ErrorMessage>{error}</ErrorMessage>}
      {maxLength && (
        <CharacterCount>
          {value.length}/{maxLength}
        </CharacterCount>
      )}
    </InputWrapper>
  );
};