import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Database,
  Search,
  Plus,
  Trash2,
  Tag,
  Clock
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { api } from '../utils/api';

interface MemoryEntry {
  id: string;
  content: string;
  tags: string[];
  created_at: string;
}

export function Memory() {
  const [searchQuery, setSearchQuery] = useState('');
  const [isAdding, setIsAdding] = useState(false);
  const [newContent, setNewContent] = useState('');
  const [newTags, setNewTags] = useState('');

  const queryClient = useQueryClient();

  const { data: searchResults, refetch: doSearch } = useQuery({
    queryKey: ['memory-search', searchQuery],
    queryFn: () =>
      searchQuery
        ? api.post('/memory/search', { query: searchQuery, limit: 20 }).then(r => r.data)
        : null,
    enabled: false,
  });

  const storeMemory = useMutation({
    mutationFn: (data: { content: string; tags: string[] }) =>
      api.post('/memory/store', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['memory-search'] });
      setIsAdding(false);
      setNewContent('');
      setNewTags('');
    },
  });

  const deleteMemory = useMutation({
    mutationFn: (id: string) => api.delete(`/memory/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['memory-search'] });
      if (searchQuery) doSearch();
    },
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery) doSearch();
  };

  const handleStore = () => {
    if (!newContent.trim()) return;
    const tags = newTags.split(',').map(t => t.trim()).filter(Boolean);
    storeMemory.mutate({ content: newContent, tags });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Memory</h1>
          <p className="mt-1 text-gray-600">
            Search and manage stored context
          </p>
        </div>
        <button
          onClick={() => setIsAdding(true)}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
        >
          <Plus className="w-4 h-4" />
          Store Memory
        </button>
      </div>

      {/* Search */}
      <form onSubmit={handleSearch} className="flex gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search memories..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <button
          type="submit"
          className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
        >
          Search
        </button>
      </form>

      {/* Results */}
      <div className="bg-white rounded-xl border border-gray-200">
        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">
            {searchResults ? `${searchResults.count} results` : 'Search Results'}
          </h2>
        </div>

        {!searchResults ? (
          <div className="p-8 text-center">
            <Database className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">Enter a search query to find memories</p>
          </div>
        ) : searchResults.count === 0 ? (
          <div className="p-8 text-center">
            <Search className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">No memories found for "{searchQuery}"</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {searchResults.results.map((entry: MemoryEntry) => (
              <MemoryRow
                key={entry.id}
                entry={entry}
                onDelete={() => deleteMemory.mutate(entry.id)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Store Memory Modal */}
      {isAdding && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-full max-w-lg bg-white rounded-xl p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Store Memory
            </h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Content
                </label>
                <textarea
                  value={newContent}
                  onChange={(e) => setNewContent(e.target.value)}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="Enter content to remember..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tags (comma-separated)
                </label>
                <input
                  type="text"
                  value={newTags}
                  onChange={(e) => setNewTags(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="tag1, tag2, tag3"
                />
              </div>

              <div className="flex justify-end gap-3">
                <button
                  onClick={() => {
                    setIsAdding(false);
                    setNewContent('');
                    setNewTags('');
                  }}
                  className="px-4 py-2 text-gray-600 hover:text-gray-900"
                >
                  Cancel
                </button>
                <button
                  onClick={handleStore}
                  disabled={storeMemory.isPending || !newContent.trim()}
                  className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
                >
                  <Plus className="w-4 h-4" />
                  {storeMemory.isPending ? 'Storing...' : 'Store'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function MemoryRow({
  entry,
  onDelete,
}: {
  entry: MemoryEntry;
  onDelete: () => void;
}) {
  return (
    <div className="p-4 hover:bg-gray-50 transition-colors">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <p className="text-gray-900 whitespace-pre-wrap">
            {entry.content}
          </p>
          <div className="flex items-center gap-4 mt-2">
            {entry.tags.length > 0 && (
              <div className="flex items-center gap-1">
                <Tag className="w-4 h-4 text-gray-400" />
                <div className="flex gap-1">
                  {entry.tags.map((tag) => (
                    <span
                      key={tag}
                      className="px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}
            <div className="flex items-center gap-1 text-xs text-gray-400">
              <Clock className="w-4 h-4" />
              {formatDistanceToNow(new Date(entry.created_at), { addSuffix: true })}
            </div>
          </div>
        </div>
        <button
          onClick={onDelete}
          className="p-2 text-gray-400 hover:text-red-600 transition-colors"
        >
          <Trash2 className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
}
