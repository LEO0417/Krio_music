import { useState, useRef, useCallback } from 'react';

export interface DragItem {
  id: string;
  index: number;
  type: string;
}

export interface DragDropOptions {
  onDragStart?: (item: DragItem) => void;
  onDragEnd?: (item: DragItem) => void;
  onDragOver?: (dragItem: DragItem, hoverItem: DragItem) => void;
  onDrop?: (dragItem: DragItem, dropItem: DragItem) => void;
  onReorder?: (dragIndex: number, hoverIndex: number) => void;
}

export const useDragAndDrop = (options: DragDropOptions = {}) => {
  const [dragState, setDragState] = useState<{
    isDragging: boolean;
    dragItem: DragItem | null;
    dragOverIndex: number | null;
  }>({
    isDragging: false,
    dragItem: null,
    dragOverIndex: null,
  });

  const dragRef = useRef<HTMLElement | null>(null);

  const handleDragStart = useCallback((
    event: React.DragEvent,
    item: DragItem
  ) => {
    event.dataTransfer.effectAllowed = 'move';
    event.dataTransfer.setData('text/plain', JSON.stringify(item));
    
    setDragState({
      isDragging: true,
      dragItem: item,
      dragOverIndex: null,
    });
    
    options.onDragStart?.(item);
  }, [options]);

  const handleDragEnd = useCallback((
    event: React.DragEvent,
    item: DragItem
  ) => {
    setDragState({
      isDragging: false,
      dragItem: null,
      dragOverIndex: null,
    });
    
    options.onDragEnd?.(item);
  }, [options]);

  const handleDragOver = useCallback((
    event: React.DragEvent,
    hoverItem: DragItem
  ) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
    
    if (!dragState.dragItem) return;
    
    if (dragState.dragItem.id === hoverItem.id) return;
    
    setDragState(prev => ({
      ...prev,
      dragOverIndex: hoverItem.index,
    }));
    
    options.onDragOver?.(dragState.dragItem, hoverItem);
  }, [dragState.dragItem, options]);

  const handleDrop = useCallback((
    event: React.DragEvent,
    dropItem: DragItem
  ) => {
    event.preventDefault();
    
    const dragData = event.dataTransfer.getData('text/plain');
    if (!dragData) return;
    
    try {
      const dragItem = JSON.parse(dragData) as DragItem;
      
      if (dragItem.id === dropItem.id) return;
      
      options.onDrop?.(dragItem, dropItem);
      options.onReorder?.(dragItem.index, dropItem.index);
      
      setDragState({
        isDragging: false,
        dragItem: null,
        dragOverIndex: null,
      });
    } catch (error) {
      console.error('Error parsing drag data:', error);
    }
  }, [options]);

  const getDragHandleProps = useCallback((item: DragItem) => ({
    draggable: true,
    onDragStart: (event: React.DragEvent) => handleDragStart(event, item),
    onDragEnd: (event: React.DragEvent) => handleDragEnd(event, item),
  }), [handleDragStart, handleDragEnd]);

  const getDropZoneProps = useCallback((item: DragItem) => ({
    onDragOver: (event: React.DragEvent) => handleDragOver(event, item),
    onDrop: (event: React.DragEvent) => handleDrop(event, item),
  }), [handleDragOver, handleDrop]);

  return {
    dragState,
    getDragHandleProps,
    getDropZoneProps,
  };
};

// Utility function to reorder array items
export const reorderItems = <T>(
  items: T[],
  startIndex: number,
  endIndex: number
): T[] => {
  const result = Array.from(items);
  const [removed] = result.splice(startIndex, 1);
  result.splice(endIndex, 0, removed);
  return result;
};