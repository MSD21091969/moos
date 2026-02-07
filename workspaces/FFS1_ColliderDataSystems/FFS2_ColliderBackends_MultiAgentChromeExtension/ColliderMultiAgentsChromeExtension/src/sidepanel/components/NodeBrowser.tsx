/**
 * NodeBrowser - Tree view component for navigating appnode structure
 * Features:
 * - Fetches nodes from DataServer API
 * - Hierarchical tree with expand/collapse
 * - Domain icons (folder for FILESYST, cloud for CLOUD, shield for ADMIN)
 * - Click handler to select node
 */
import { useState, useEffect, useMemo, useCallback } from "react"

export interface AppNode {
    id: string
    path: string
    container: {
        manifest: Record<string, unknown>
        instructions: string[]
        rules: string[]
        skills: string[]
        tools: unknown[]
        knowledge: string[]
        workflows: unknown[]
        configs: Record<string, unknown>
    }
    node_metadata: Record<string, unknown>
}

export type Domain = "FILESYST" | "CLOUD" | "ADMIN"

interface TreeNode extends AppNode {
    children: TreeNode[]
    isExpanded: boolean
}

interface NodeBrowserProps {
    nodes: AppNode[]
    domain: Domain
    selectedPath?: string
    onSelect: (node: AppNode) => void
    onRefresh?: () => void
    isLoading?: boolean
}

/**
 * Build tree structure from flat node list
 */
function buildTree(nodes: AppNode[]): TreeNode[] {
    const nodeMap = new Map<string, TreeNode>()
    const roots: TreeNode[] = []

    // Sort nodes by path to ensure parents come before children
    const sorted = [...nodes].sort((a, b) => a.path.localeCompare(b.path))

    for (const node of sorted) {
        const treeNode: TreeNode = {
            ...node,
            children: [],
            isExpanded: node.path === "/" || node.path.split("/").length <= 2,
        }
        nodeMap.set(node.path, treeNode)

        // Find parent path
        const parentPath = getParentPath(node.path)

        if (parentPath === null || !nodeMap.has(parentPath)) {
            roots.push(treeNode)
        } else {
            const parent = nodeMap.get(parentPath)
            parent?.children.push(treeNode)
        }
    }

    return roots
}

function getParentPath(path: string): string | null {
    if (path === "/") return null
    const parts = path.split("/").filter(Boolean)
    if (parts.length === 1) return "/"
    return "/" + parts.slice(0, -1).join("/")
}

/**
 * Get domain-specific icon for a node
 */
function getDomainIcon(domain: Domain, hasChildren: boolean): string {
    if (hasChildren) {
        switch (domain) {
            case "FILESYST": return "📁"
            case "CLOUD": return "☁️"
            case "ADMIN": return "🛡️"
        }
    }
    switch (domain) {
        case "FILESYST": return "📄"
        case "CLOUD": return "📡"
        case "ADMIN": return "🔐"
    }
}

/**
 * Get the display name for a node path
 */
function getNodeName(path: string): string {
    if (path === "/") return "Root"
    const parts = path.split("/").filter(Boolean)
    return parts[parts.length - 1] || path
}

interface TreeItemProps {
    node: TreeNode
    domain: Domain
    level: number
    selectedPath?: string
    expandedPaths: Set<string>
    onSelect: (node: AppNode) => void
    onToggle: (path: string) => void
}

function TreeItem({
    node,
    domain,
    level,
    selectedPath,
    expandedPaths,
    onSelect,
    onToggle,
}: TreeItemProps) {
    const isExpanded = expandedPaths.has(node.path)
    const hasChildren = node.children.length > 0
    const isSelected = selectedPath === node.path

    return (
        <div>
            <div
                style={{
                    ...styles.treeItem,
                    paddingLeft: 12 + level * 16,
                    ...(isSelected ? styles.treeItemSelected : {}),
                }}
                onClick={() => onSelect(node)}
            >
                {/* Expand/Collapse Toggle */}
                {hasChildren ? (
                    <button
                        style={styles.expandButton}
                        onClick={(e) => {
                            e.stopPropagation()
                            onToggle(node.path)
                        }}
                    >
                        {isExpanded ? "▼" : "▶"}
                    </button>
                ) : (
                    <span style={styles.expandPlaceholder} />
                )}

                {/* Icon */}
                <span style={styles.nodeIcon}>
                    {getDomainIcon(domain, hasChildren)}
                </span>

                {/* Name */}
                <span style={styles.nodeName}>{getNodeName(node.path)}</span>

                {/* Stats badges */}
                <div style={styles.nodeBadges}>
                    {node.container.tools.length > 0 && (
                        <span style={styles.badge} title="Tools">
                            🔧 {node.container.tools.length}
                        </span>
                    )}
                    {node.container.knowledge.length > 0 && (
                        <span style={styles.badge} title="Knowledge">
                            📚 {node.container.knowledge.length}
                        </span>
                    )}
                </div>
            </div>

            {/* Children */}
            {hasChildren && isExpanded && (
                <div>
                    {node.children.map((child) => (
                        <TreeItem
                            key={child.path}
                            node={child}
                            domain={domain}
                            level={level + 1}
                            selectedPath={selectedPath}
                            expandedPaths={expandedPaths}
                            onSelect={onSelect}
                            onToggle={onToggle}
                        />
                    ))}
                </div>
            )}
        </div>
    )
}

export function NodeBrowser({
    nodes,
    domain,
    selectedPath,
    onSelect,
    onRefresh,
    isLoading,
}: NodeBrowserProps) {
    const [expandedPaths, setExpandedPaths] = useState<Set<string>>(
        new Set(["/"])
    )
    const [searchQuery, setSearchQuery] = useState("")

    // Build tree structure
    const tree = useMemo(() => buildTree(nodes), [nodes])

    // Filter nodes by search query
    const filteredTree = useMemo(() => {
        if (!searchQuery.trim()) return tree

        const query = searchQuery.toLowerCase()

        function filterNode(node: TreeNode): TreeNode | null {
            const matchesQuery =
                node.path.toLowerCase().includes(query) ||
                getNodeName(node.path).toLowerCase().includes(query)

            const filteredChildren = node.children
                .map(filterNode)
                .filter((n): n is TreeNode => n !== null)

            if (matchesQuery || filteredChildren.length > 0) {
                return { ...node, children: filteredChildren, isExpanded: true }
            }

            return null
        }

        return tree.map(filterNode).filter((n): n is TreeNode => n !== null)
    }, [tree, searchQuery])

    // Auto-expand to selected node
    useEffect(() => {
        if (selectedPath && selectedPath !== "/") {
            const paths = new Set(expandedPaths)
            const parts = selectedPath.split("/").filter(Boolean)
            let current = ""
            for (const part of parts.slice(0, -1)) {
                current = `${current}/${part}`
                paths.add(current)
            }
            paths.add("/")
            setExpandedPaths(paths)
        }
    }, [selectedPath])

    const handleToggle = useCallback((path: string) => {
        setExpandedPaths((prev) => {
            const next = new Set(prev)
            if (next.has(path)) {
                next.delete(path)
            } else {
                next.add(path)
            }
            return next
        })
    }, [])

    const expandAll = useCallback(() => {
        const allPaths = new Set<string>()
        function collectPaths(nodes: TreeNode[]) {
            for (const node of nodes) {
                allPaths.add(node.path)
                collectPaths(node.children)
            }
        }
        collectPaths(tree)
        setExpandedPaths(allPaths)
    }, [tree])

    const collapseAll = useCallback(() => {
        setExpandedPaths(new Set(["/"]))
    }, [])

    return (
        <div style={styles.container}>
            {/* Search & Actions Bar */}
            <div style={styles.toolbar}>
                <input
                    type="text"
                    placeholder="Search nodes..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    style={styles.searchInput}
                />
                <div style={styles.toolbarActions}>
                    <button
                        onClick={expandAll}
                        style={styles.toolbarButton}
                        title="Expand all"
                    >
                        ⊞
                    </button>
                    <button
                        onClick={collapseAll}
                        style={styles.toolbarButton}
                        title="Collapse all"
                    >
                        ⊟
                    </button>
                    {onRefresh && (
                        <button
                            onClick={onRefresh}
                            style={styles.toolbarButton}
                            title="Refresh"
                            disabled={isLoading}
                        >
                            {isLoading ? "⟳" : "↻"}
                        </button>
                    )}
                </div>
            </div>

            {/* Tree Content */}
            <div style={styles.treeContainer}>
                {isLoading && nodes.length === 0 ? (
                    <div style={styles.loading}>Loading nodes...</div>
                ) : filteredTree.length === 0 ? (
                    <div style={styles.empty}>
                        {searchQuery ? "No matching nodes" : "No nodes found"}
                    </div>
                ) : (
                    filteredTree.map((node) => (
                        <TreeItem
                            key={node.path}
                            node={node}
                            domain={domain}
                            level={0}
                            selectedPath={selectedPath}
                            expandedPaths={expandedPaths}
                            onSelect={onSelect}
                            onToggle={handleToggle}
                        />
                    ))
                )}
            </div>

            {/* Stats Footer */}
            <div style={styles.footer}>
                <span>{nodes.length} nodes</span>
                {selectedPath && <span>Selected: {selectedPath}</span>}
            </div>
        </div>
    )
}

const styles: Record<string, React.CSSProperties> = {
    container: {
        display: "flex",
        flexDirection: "column",
        height: "100%",
        backgroundColor: "#0f0f23",
        color: "#e2e8f0",
    },
    toolbar: {
        display: "flex",
        gap: "8px",
        padding: "8px 12px",
        borderBottom: "1px solid #1e293b",
        alignItems: "center",
    },
    searchInput: {
        flex: 1,
        padding: "6px 10px",
        borderRadius: "6px",
        border: "1px solid #334155",
        background: "#1e293b",
        color: "#e2e8f0",
        fontSize: "13px",
        outline: "none",
    },
    toolbarActions: {
        display: "flex",
        gap: "4px",
    },
    toolbarButton: {
        padding: "4px 8px",
        background: "#1e293b",
        border: "1px solid #334155",
        borderRadius: "4px",
        color: "#e2e8f0",
        cursor: "pointer",
        fontSize: "14px",
    },
    treeContainer: {
        flex: 1,
        overflowY: "auto",
        overflowX: "hidden",
        padding: "8px 0",
    },
    treeItem: {
        display: "flex",
        alignItems: "center",
        gap: "6px",
        padding: "6px 12px",
        cursor: "pointer",
        borderRadius: "4px",
        margin: "1px 4px",
        transition: "background 0.1s",
    },
    treeItemSelected: {
        background: "linear-gradient(135deg, rgba(99, 102, 241, 0.3), rgba(139, 92, 246, 0.3))",
        borderLeft: "2px solid #818cf8",
    },
    expandButton: {
        width: "16px",
        height: "16px",
        padding: 0,
        background: "none",
        border: "none",
        color: "#64748b",
        cursor: "pointer",
        fontSize: "10px",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
    },
    expandPlaceholder: {
        width: "16px",
        height: "16px",
    },
    nodeIcon: {
        fontSize: "14px",
        flexShrink: 0,
    },
    nodeName: {
        flex: 1,
        fontSize: "13px",
        overflow: "hidden",
        textOverflow: "ellipsis",
        whiteSpace: "nowrap",
    },
    nodeBadges: {
        display: "flex",
        gap: "4px",
        fontSize: "10px",
        opacity: 0.7,
    },
    badge: {
        padding: "2px 4px",
        background: "#1e293b",
        borderRadius: "3px",
    },
    footer: {
        display: "flex",
        justifyContent: "space-between",
        padding: "8px 12px",
        fontSize: "11px",
        opacity: 0.6,
        borderTop: "1px solid #1e293b",
    },
    loading: {
        display: "flex",
        justifyContent: "center",
        padding: "20px",
        opacity: 0.6,
    },
    empty: {
        display: "flex",
        justifyContent: "center",
        padding: "20px",
        opacity: 0.6,
    },
}

export default NodeBrowser
