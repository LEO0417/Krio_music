import { renderHook, act } from '@testing-library/react';
import { useDragAndDrop, reorderItems } from '../useDragAndDrop';

describe('useDragAndDrop Hook', () => {
  const mockCallbacks = {
    onDragStart: jest.fn(),
    onDragEnd: jest.fn(),
    onDragOver: jest.fn(),
    onDrop: jest.fn(),
    onReorder: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('initializes with default state', () => {
    const { result } = renderHook(() => useDragAndDrop());
    
    expect(result.current.dragState.isDragging).toBe(false);
    expect(result.current.dragState.dragItem).toBe(null);
    expect(result.current.dragState.dragOverIndex).toBe(null);
  });

  it('provides drag handle props', () => {
    const { result } = renderHook(() => useDragAndDrop());
    
    const dragItem = { id: 'item1', index: 0, type: 'test' };
    const props = result.current.getDragHandleProps(dragItem);
    
    expect(props.draggable).toBe(true);
    expect(typeof props.onDragStart).toBe('function');
    expect(typeof props.onDragEnd).toBe('function');
  });

  it('provides drop zone props', () => {
    const { result } = renderHook(() => useDragAndDrop());
    
    const dropItem = { id: 'item1', index: 0, type: 'test' };
    const props = result.current.getDropZoneProps(dropItem);
    
    expect(typeof props.onDragOver).toBe('function');
    expect(typeof props.onDrop).toBe('function');
  });

  it('handles drag start', () => {
    const { result } = renderHook(() => useDragAndDrop(mockCallbacks));
    
    const dragItem = { id: 'item1', index: 0, type: 'test' };
    const mockEvent = {
      dataTransfer: {
        effectAllowed: '',
        setData: jest.fn(),
      },
    } as any;
    
    const props = result.current.getDragHandleProps(dragItem);
    
    act(() => {
      props.onDragStart(mockEvent);
    });
    
    expect(result.current.dragState.isDragging).toBe(true);
    expect(result.current.dragState.dragItem).toEqual(dragItem);
    expect(mockEvent.dataTransfer.effectAllowed).toBe('move');
    expect(mockEvent.dataTransfer.setData).toHaveBeenCalledWith('text/plain', JSON.stringify(dragItem));
    expect(mockCallbacks.onDragStart).toHaveBeenCalledWith(dragItem);
  });

  it('handles drag end', () => {
    const { result } = renderHook(() => useDragAndDrop(mockCallbacks));
    
    const dragItem = { id: 'item1', index: 0, type: 'test' };
    const mockEvent = {} as any;
    
    // Start drag first
    act(() => {
      result.current.dragState.isDragging = true;
      result.current.dragState.dragItem = dragItem;
    });
    
    const props = result.current.getDragHandleProps(dragItem);
    
    act(() => {
      props.onDragEnd(mockEvent);
    });
    
    expect(result.current.dragState.isDragging).toBe(false);
    expect(result.current.dragState.dragItem).toBe(null);
    expect(mockCallbacks.onDragEnd).toHaveBeenCalledWith(dragItem);
  });

  it('handles drag over', () => {
    const { result } = renderHook(() => useDragAndDrop(mockCallbacks));
    
    const hoverItem = { id: 'item2', index: 1, type: 'test' };
    const mockEvent = {
      preventDefault: jest.fn(),
      dataTransfer: {
        dropEffect: '',
      },
    } as any;
    
    // Set up drag state
    act(() => {
      result.current.dragState.isDragging = true;
      result.current.dragState.dragItem = { id: 'item1', index: 0, type: 'test' };
    });
    
    const props = result.current.getDropZoneProps(hoverItem);
    
    act(() => {
      props.onDragOver(mockEvent);
    });
    
    expect(mockEvent.preventDefault).toHaveBeenCalled();
    expect(mockEvent.dataTransfer.dropEffect).toBe('move');
    expect(result.current.dragState.dragOverIndex).toBe(1);
  });

  it('handles drop', () => {
    const { result } = renderHook(() => useDragAndDrop(mockCallbacks));
    
    const dragItem = { id: 'item1', index: 0, type: 'test' };
    const dropItem = { id: 'item2', index: 1, type: 'test' };
    const mockEvent = {
      preventDefault: jest.fn(),
      dataTransfer: {
        getData: jest.fn(() => JSON.stringify(dragItem)),
      },
    } as any;
    
    const props = result.current.getDropZoneProps(dropItem);
    
    act(() => {
      props.onDrop(mockEvent);
    });
    
    expect(mockEvent.preventDefault).toHaveBeenCalled();
    expect(mockEvent.dataTransfer.getData).toHaveBeenCalledWith('text/plain');
    expect(mockCallbacks.onDrop).toHaveBeenCalledWith(dragItem, dropItem);
    expect(mockCallbacks.onReorder).toHaveBeenCalledWith(0, 1);
  });

  it('ignores drop on same item', () => {
    const { result } = renderHook(() => useDragAndDrop(mockCallbacks));
    
    const item = { id: 'item1', index: 0, type: 'test' };
    const mockEvent = {
      preventDefault: jest.fn(),
      dataTransfer: {
        getData: jest.fn(() => JSON.stringify(item)),
      },
    } as any;
    
    const props = result.current.getDropZoneProps(item);
    
    act(() => {
      props.onDrop(mockEvent);
    });
    
    expect(mockCallbacks.onDrop).not.toHaveBeenCalled();
    expect(mockCallbacks.onReorder).not.toHaveBeenCalled();
  });

  it('handles invalid drag data', () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    const { result } = renderHook(() => useDragAndDrop(mockCallbacks));
    
    const dropItem = { id: 'item2', index: 1, type: 'test' };
    const mockEvent = {
      preventDefault: jest.fn(),
      dataTransfer: {
        getData: jest.fn(() => 'invalid json'),
      },
    } as any;
    
    const props = result.current.getDropZoneProps(dropItem);
    
    act(() => {
      props.onDrop(mockEvent);
    });
    
    expect(consoleSpy).toHaveBeenCalledWith('Error parsing drag data:', expect.any(SyntaxError));
    
    consoleSpy.mockRestore();
  });
});

describe('reorderItems utility', () => {
  it('reorders items correctly', () => {
    const items = ['a', 'b', 'c', 'd'];
    const result = reorderItems(items, 0, 2);
    
    expect(result).toEqual(['b', 'c', 'a', 'd']);
  });

  it('handles moving item to end', () => {
    const items = ['a', 'b', 'c', 'd'];
    const result = reorderItems(items, 0, 3);
    
    expect(result).toEqual(['b', 'c', 'd', 'a']);
  });

  it('handles moving item to beginning', () => {
    const items = ['a', 'b', 'c', 'd'];
    const result = reorderItems(items, 3, 0);
    
    expect(result).toEqual(['d', 'a', 'b', 'c']);
  });

  it('handles moving item backwards', () => {
    const items = ['a', 'b', 'c', 'd'];
    const result = reorderItems(items, 3, 1);
    
    expect(result).toEqual(['a', 'd', 'b', 'c']);
  });

  it('returns original array when moving to same position', () => {
    const items = ['a', 'b', 'c', 'd'];
    const result = reorderItems(items, 1, 1);
    
    expect(result).toEqual(['a', 'b', 'c', 'd']);
  });

  it('does not mutate original array', () => {
    const items = ['a', 'b', 'c', 'd'];
    const original = [...items];
    
    reorderItems(items, 0, 2);
    
    expect(items).toEqual(original);
  });
});