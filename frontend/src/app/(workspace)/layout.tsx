export default function WorkspaceLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top nav bar */}
      <header className="h-12 border-b border-gray-200 bg-white flex items-center px-4">
        <span className="text-sm font-semibold text-amber-600">
          金手指 AI 编剧助手
        </span>
      </header>
      {children}
    </div>
  );
}
