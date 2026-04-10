export default function WorkspaceLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-[#F0EDE8]">
      {/* Top nav bar */}
      <header className="h-12 border-b border-[#E8E4DC] bg-[#FAFAF8] flex items-center px-4">
        <span className="text-sm font-semibold text-[#C8974A]">
          金手指 AI 编剧助手
        </span>
      </header>
      {children}
    </div>
  );
}
