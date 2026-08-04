const home = document.querySelector(".home");
const canvas = document.querySelector(".canvas-shell");
const projectsEl = document.querySelector("#projects");
const projectCount = document.querySelector("#project-count");
const canvasTitle = document.querySelector("#canvas-title");
const createForm = document.querySelector("#create-project");
const deleteActiveProject = document.querySelector("#delete-active-project");
const documentForm = document.querySelector("#document-form");
const imageFile = document.querySelector("#image-file");
const imageFileName = document.querySelector("#image-file-name");
const paperFile = document.querySelector("#paper-file");
const paperFileName = document.querySelector("#paper-file-name");
const importPaperButton = document.querySelector("#import-paper-pdf");
const clearDocumentInputsButton = document.querySelector("#clear-document-inputs");
const undoCurrentStepButton = document.querySelector("#undo-current-step");
const documentOutput = document.querySelector("#document-output");
const documentStatus = document.querySelector("#document-status");
const canvasStatus = document.querySelector("#canvas-status");
const canvasOutput = document.querySelector("#canvas-output");
const modelStatus = document.querySelector("#model-status");
const modelOutput = document.querySelector("#model-output");
const autosaveStatus = document.querySelector("#autosave-status");
const exportPdfButton = document.querySelector("#export-pdf");
const workspaceMain = document.querySelector(".workspace-main");
const workspace = document.querySelector(".workspace");
const canvasContent = document.querySelector("#canvas-content");
const canvasPlane = document.querySelector("#canvas-plane");
const nodesLayer = document.querySelector("#nodes");
const edgesLayer = document.querySelector("#edges");
const zoomOut = document.querySelector("#zoom-out");
const zoomIn = document.querySelector("#zoom-in");
const zoomLevel = document.querySelector("#zoom-level");
const themeToggles = document.querySelectorAll("[data-theme-toggle]");
const nodeMenu = document.querySelector("#node-menu");
const menuOpenFull = document.querySelector("[data-menu-open-full]");
const menuDelete = document.querySelector("[data-menu-delete]");
const textReader = document.querySelector("#text-reader");
const textReaderTitle = document.querySelector("#text-reader-title");
const textReaderBody = document.querySelector("#text-reader-body");
const closeReader = document.querySelector("[data-close-reader]");
const imageViewer = document.querySelector("#image-viewer");
const imageViewerTitle = document.querySelector("#image-viewer-title");
const imageViewerImg = document.querySelector("#image-viewer-img");
const imageViewerCaption = document.querySelector("#image-viewer-caption");
const closeImageViewerButton = document.querySelector("[data-close-image-viewer]");
const apiAccessGate = document.querySelector("#api-access-gate");
const apiAccessForm = document.querySelector("#api-access-form");
const apiAccessKey = document.querySelector("#api-access-key");
const apiAccessError = document.querySelector("#api-access-error");
const appShell = document.querySelector("#app-shell");
const conversationTitle = document.querySelector("#conversation-title");
const conversationPolicy = document.querySelector("#conversation-policy");
const conversationProgress = document.querySelector("#conversation-progress");
const conversationGuideActions = document.querySelector("#conversation-guide-actions");
const conversationMessages = document.querySelector("#conversation-messages");
const conversationHistoryDialog = document.querySelector("#conversation-history-dialog");
const conversationHistoryDialogMessages = document.querySelector("#conversation-history-dialog-messages");
const conversationHistoryClose = document.querySelector("#conversation-history-close");
const conversationForm = document.querySelector("#conversation-form");
const conversationInput = document.querySelector("#conversation-input");
const conversationPerspectiveButtons = document.querySelectorAll("[data-conversation-perspective]");
const conversationDock = document.querySelector(".conversation-dock");
const conversationScopeIndicator = document.querySelector("#conversation-scope-indicator");
const scopeViewTitle = document.querySelector("#scope-view-title");
const scopeNodeCount = document.querySelector("#scope-node-count");
const stagePresentation = document.querySelector("#stage-presentation");
const workflowStrip = document.querySelector("#workflow-strip");
const canvasPreview = document.querySelector("#canvas-preview");
const canvasPreviewViewport = document.querySelector("#canvas-preview-viewport");
const canvasPreviewPlane = document.querySelector("#canvas-preview-plane");
const openCanvasFocusButton = document.querySelector("#open-canvas-focus");
const canvasPreviewTooltip = document.querySelector("#canvas-preview-tooltip");
const scopeList = document.querySelector("#scope-list");
const commandProposals = document.querySelector("#command-proposals");
const navigatorRevision = document.querySelector("#navigator-revision");
const toolSidebarList = document.querySelector("#tool-sidebar-list");
const returnLocalScope = document.querySelector("#return-local-scope");
const canvasFocusLayer = document.querySelector("#canvas-focus-layer");
const canvasFocusTitle = document.querySelector("#canvas-focus-title");
const closeCanvasFocusButton = document.querySelector("#close-canvas-focus");

let activeProject = null;
let activeCanvas = null;
let activeInteraction = null;
let activeProjection = null;
let activeSessionId = null;
let activeScopeId = null;
let previewFocusedStageId = "";
let dragState = null;
let connectionDraft = null;
let panState = null;
let contextNodeId = null;
let contextEdgeId = null;
let zoom = 1;
let spacePressed = false;
let tabApiKey = "";
let conversationPerspective = "research";
let uiActionInFlight = false;
const AGENT_GUIDE_CACHE_KEY = "speculative-web-agent-guide-cache-v2";
const agentGuideCache = loadAgentGuideCache();
const agentGuideInFlight = new Set();
const branchImageInFlight = new Set();
let branchImageQueueRunning = false;
const quickInputSelections = new Map();
let autosaveTimer = null;
let autosaveStatusTimer = null;
let modelAccess = {
  openaiApiKeyConfigured: false,
  openaiRunsEnabled: true,
  userApiKeyRequired: true,
};
const conversationHistoryState = new Map();
const MIN_ZOOM = 0.25;
const MAX_ZOOM = 1;
const ZOOM_STEP = 0.25;
const THEME_KEY = "speculative-web-theme";
const LOCALE_KEY = "speculative-web-locale";
const translations = {
  en: {
    "document.title": "Speculative Web",
    "home.eyebrow": "Speculative Design Graph System",
    "home.title": "Canvas",
    "home.newCanvas": "New canvas",
    "home.existingCanvases": "Existing canvases",
    "home.existing": "Existing",
    "canvas.workspace": "Canvas workspace",
    "canvas.active": "Active Canvas",
    "canvas.delete": "Delete Canvas",
    "canvas.tools": "Canvas tools",
    "canvas.zoomOut": "Zoom out",
    "canvas.zoomIn": "Zoom in",
    "common.create": "Create",
    "common.index": "Index",
    "common.chooseFile": "Choose File",
    "common.chooseImage": "Choose Image",
    "common.choosePaper": "Choose paper PDF",
    "common.noFile": "No file selected",
    "common.read": "Read",
    "common.importPaper": "Import paper",
    "common.clear": "Clear",
    "common.open": "Open",
    "common.delete": "Delete",
    "common.close": "Close",
    "common.run": "Run",
    "common.running": "Running",
    "common.exportPdf": "Export PDF",
    "common.output": "output",
    "common.inputText": "input text",
    "common.openFullText": "Open Full Text",
    "common.document": "document",
    "common.semanticImage": "semantic image",
    "common.generatedImage": "Generated speculative image",
    "nodes.text": "Text",
    "nodes.conversation": "Conversation",
    "nodes.upload": "Upload",
    "nodes.image": "Image",
    "nodes.multimodal": "Text+Image",
    "nodes.modify": "Modify",
    "nodes.tool": "Tool",
    "nodes.operation": "Operation",
    "nodes.guidedScenario": "Guided Scenario",
    "sidebar.create": "Create nodes",
    "sidebar.textNode": "Text note",
    "sidebar.conversationNode": "Conversation",
    "sidebar.uploadSource": "Upload source",
    "sidebar.imageNode": "Image node",
    "sidebar.methodNode": "Method node",
    "sidebar.operationNode": "Operation node",
    "sidebar.scenarioNode": "Guided scenario",
    "sidebar.startFlow": "Start guided flow",
    "workflow.start": "Start Four Futures flow",
    "workflow.eyebrow": "Guided foundation",
    "workflow.dialogTitle": "Frame a research inquiry",
    "workflow.dialogIntro": "Create an editable research brief and a ready four-futures operation. No model, tool, or image action happens here.",
    "workflow.startMode": "Starting point",
    "workflow.modeResearch": "Real research / researcher-led",
    "workflow.modeDesign": "Design proposition / designer-led",
    "workflow.topic": "Research topic",
    "workflow.topicPlaceholder": "What should this inquiry examine?",
    "workflow.focus": "Research focus",
    "workflow.focusPlaceholder": "What needs attention, evidence, or reframing?",
    "workflow.assumptions": "Default assumptions",
    "workflow.stakeholders": "Stakeholders",
    "workflow.tensions": "Core tensions",
    "workflow.listPlaceholder": "One item per line",
    "workflow.create": "Create foundation",
    "workflow.choose": "Choose this future",
    "workflow.chosen": "Selected for discussion",
    "workflow.awaitingSelection": "Compare and choose a future",
    "workflow.inputManual": "Enter by cards",
    "workflow.inputConversation": "Or describe it in the conversation below",
    "workflow.inputReady": "Input cards are ready to edit directly on the canvas.",
    "workflow.undoStep": "Undo step",
    "workflow.undoStepConfirm": "Undo this workflow step and remove its generated cards/nodes?",
    "workflow.undoStepDone": "Current workflow step has been undone.",
    "document.onlyPaperPdf": "Only PDF papers can be imported.",
    "document.noReadableFile": "Choose an image or paper PDF first.",
    "document.imageImported": "Image input node added to the canvas.",
    "document.paperImported": "Paper imported into the research inquiry cards.",
    "workflow.chooseOne": "Choose exactly one direction",
    "workflow.toolsHint": "Choose one or more tools in the left rail, then generate one scenario.",
    "workflow.scenarioReady": "Current scenario generated",
    "workflow.imageGenerating": "Image generating",
    "workflow.imageFailed": "Image unavailable",
    "workflow.expandText": "Open text",
    "nodes.textTitle": "Text Node",
    "nodes.conversationTitle": "Conversation",
    "nodes.uploadTitle": "Upload",
    "nodes.imageTitle": "Image Node",
    "nodes.multimodalTitle": "Text+Image Node",
    "nodes.modifyTitle": "Modify",
    "nodes.operationTitle": "Operation Node",
    "nodes.textDefault": "New text information node.",
    "nodes.conversationDefault": "Conversation or intermediate thinking content.",
    "nodes.imageDefault": "Image semantic summary placeholder.",
    "nodes.operationDefault": "Configurable operation definition.",
    "output.text": "Text",
    "output.image": "Image",
    "output.multimodal": "Text+Image",
    "status.idle": "idle",
    "status.loading": "loading",
    "status.ready": "ready",
    "status.checking": "checking",
    "status.configured": "configured",
    "status.offline": "offline",
    "status.reading": "reading",
    "status.importing": "importing",
    "status.running": "running",
    "status.deleting": "deleting",
    "status.error": "error",
    "status.draft": "draft",
    "status.success": "success",
    "status.failed": "failed",
    "status.stale": "stale",
    "status.generated": "generated",
    "status.orphaned": "orphaned",
    "status.pending": "pending",
    "status.active": "active",
    "status.succeeded": "succeeded",
    "status.complete": "complete",
    "autosave.saved": "Auto-saved",
    "autosave.saving": "Saving...",
    "autosave.error": "Save failed",
    "export.title": "Speculative Web Export",
    "export.cards": "Cards",
    "export.canvasNodes": "Canvas nodes",
    "export.chat": "Chat record",
    "export.noMessages": "No chat record yet.",
    "export.generatedAt": "Generated at",
    "export.printHint": "Use the print dialog to save this report as PDF.",
    "inspector.canvasSnapshot": "Canvas Snapshot",
    "inspector.openCanvas": "Open a canvas to inspect its graph state.",
    "inspector.modelApi": "Model API",
    "inspector.modelStatus": "Model service status will appear here.",
    "inspector.documentIntake": "Document Intake",
    "inspector.documentPrompt": "Upload PDF, DOCX, TXT, or MD to inspect extracted structure.",
    "menu.nodeActions": "Node actions",
    "menu.deleteNode": "Delete Node",
    "menu.deleteEdge": "Delete Edge",
    "reader.nodeText": "Node Text",
    "reader.generatedOutput": "Generated Output",
    "reader.nodeImage": "Node Image",
    "reader.imagePreview": "Image Preview",
    "reader.noText": "No text content.",
    "reader.imagePrompt": "Image prompt",
    "reader.semanticSummary": "Semantic summary",
    "reader.imageUrl": "Image URL",
    "reader.imageError": "Image error",
    "project.nodes": "{count} nodes",
    "project.renameHint": "double-click to rename",
    "project.deleteLabel": "Delete canvas {title}",
    "project.renamePrompt": "Rename canvas",
    "project.untitled": "Untitled Canvas",
    "project.deleteConfirm": "Delete canvas \"{title}\" and all of its nodes, edges, and runs?",
    "node.deleteConfirm": "Delete node \"{title}\" and its connections?",
    "node.imageFallback": "Image semantic summary placeholder.",
    "node.imageReference": "Image reference",
    "node.noImageUploaded": "No image uploaded",
    "node.multimodalFallback": "Text+image output placeholder.",
    "node.uploadPrompt": "Upload PDF, DOCX, TXT, or MD.",
    "node.noFileUploaded": "No file uploaded",
    "node.openImage": "Open image preview",
    "node.inputPort": "Input port",
    "node.outputPort": "Output port",
    "node.revision": "revision {count}",
    "generate.aria": "Generating content",
    "theme.dark": "Dark",
    "theme.light": "Light",
    "composition.parallel": "parallel",
    "composition.sequential": "sequential",
    "composition.synthesis": "synthesis",
    "access.eyebrow": "Private API Access",
    "access.title": "Enter your API key",
    "access.label": "OpenAI API key",
    "access.placeholder": "Paste an API key for this tab",
    "access.notice": "The key stays only in this tab's memory and is sent only when you run a model operation. Refreshing the page clears it.",
    "access.continue": "Continue",
    "access.invalid": "Enter a valid API key to continue.",
    "access.required": "Enter your API key before running a model operation.",
    "access.active": "A personal API key is active for this tab. It is never saved by this site.",
    "access.serverActive": "Model service ready.",
    "conversation.eyebrow": "Conversation",
    "conversation.emptyTitle": "Working thread",
    "conversation.inputLabel": "Add to conversation",
    "conversation.placeholder": "Add a research instruction for this scope",
    "conversation.send": "Send",
    "conversation.scope": "Scope",
    "conversation.policy.confirm": "confirm",
    "conversation.none": "No messages in this scope yet.",
    "conversation.history": "Conversation history",
    "conversation.historyHint": "Scroll to review the full thread.",
    "conversation.nodeEdited": "Node edited directly",
    "conversation.nodeRemoved": "Node removed directly",
    "conversation.branchInvalidated": "This speculation was removed from the current flow",
    "conversation.superseded": "This speculation no longer participates in the current flow",
    "conversation.toolsChanged": "Discussion methods updated",
    "conversation.user": "researcher",
    "conversation.assistant": "assistant",
    "conversation.system": "system",
    "conversation.scientistInput": "Scientist input",
    "conversation.designerInput": "Designer input",
    "conversation.startResearch": "Start with real research",
    "conversation.startDesign": "Start with a design proposition",
    "conversation.perspectiveStart": "Starting point",
    "conversation.perspectiveInput": "This input",
    "conversation.quickPrefix": "Quick input option",
    "conversation.quickSelected": "selected",
    "conversation.quickConfirmHint": "Select one or more options, then press Send.",
    "conversation.quickLoading": "Loading options...",
    "conversation.generateScenario": "Generate text-image scenario",
    "conversation.agentIntro": "AI host: describe a research condition or design proposition. I will keep asking who uses it, who is affected, and where uncertainty appears.",
    "conversation.agentPrompt": "AI host",
    "conversation.runWhatIf": "Generate four What-if lines",
    "workflow.card01": "Research issue",
    "workflow.card02": "Keywords",
    "workflow.card03": "WHAT-IF",
    "workflow.card04": "Tools",
    "workflow.card05": "Scenario generation",
    "workflow.cardWaiting": "Awaiting conversation",
    "workflow.cardReady": "Ready to review",
    "workflow.cardPending": "Waiting for prior step",
    "workflow.initial01": "Choose Scientist input or Designer input below, then describe the material in one sentence.",
    "workflow.initial02": "The agent will split the issue into keywords, default assumptions, and stakeholders.",
    "workflow.initial03": "After keywords are confirmed, generate growth, collapse, balance, and transformation lines.",
    "workflow.initial04": "Apply a method tool to the current node and write its result back into the process.",
    "workflow.initial05": "Generate scenario text, image materials, and exportable review logic.",
    "scope.eyebrow": "Current nodes",
    "scope.loading": "Loading scope",
    "scope.global": "Global graph",
    "scope.returnLocal": "Return to local",
    "navigator.eyebrow": "Canvas preview",
    "navigator.title": "Overview",
    "navigator.openGlobal": "Open global graph",
    "navigator.openCanvas": "Open node canvas",
    "navigator.hint": "Select a local scope to return to its focused graph.",
    "navigator.scopes": "Scopes",
    "navigator.proposals": "Command proposals",
    "navigator.none": "No pending proposals.",
    "toolSidebar.eyebrow": "Tool nodes",
    "toolSidebar.title": "Tools",
    "toolSidebar.none": "No Modify tools in this scope.",
    "toolSidebar.nodeType": "tool",
    "toolSidebar.selected": "selected",
    "toolSidebar.remove": "Remove",
    "toolSidebar.toModify": "to Modify",
    "toolSidebar.required": "Choose at least one method for this discussion.",
    "toolSidebar.recommended": "Recommended",
    "modify.toolsInSidebar": "{count} tool nodes in sidebar",
    "workflowStrip.eyebrow": "Guided process",
    "workflowStrip.brief": "Research brief",
    "workflowStrip.keywords": "Keywords",
    "workflowStrip.whatIf": "What-if directions",
    "workflowStrip.methods": "Methods & tools",
    "workflowStrip.outcomes": "Scenario output",
    "workflowStrip.ready": "Ready",
    "workflowStrip.active": "In progress",
    "workflowStrip.awaiting": "Awaiting input",
    "workflowStrip.empty": "No process stages are available yet.",
    "stagePresentation.current": "Current stage",
    "stagePresentation.scope": "Attached scope",
    "stagePresentation.methods": "Selected methods",
    "stagePresentation.outputs": "Ready outputs",
    "stagePresentation.noMethods": "Choose a method when this stage needs one.",
    "stagePresentation.moreMethods": "+{count} more",
    "canvasFocus.eyebrow": "Node canvas",
    "canvasFocus.close": "Return to process",
    "canvasFocus.zoomControls": "Canvas zoom controls",
    "operation.definition": "definition",
    "operation.toolsSelected": "{count} tools",
    "command.approve": "Approve",
    "command.reject": "Reject",
    "command.proposed": "proposed",
    "command.approved": "approved",
    "command.rejected": "rejected",
    "command.applied": "applied",
    "command.superseded": "superseded",
  },
  zh: {
    "document.title": "思辨设计画布",
    "home.eyebrow": "思辨设计图谱系统",
    "home.title": "画布",
    "home.newCanvas": "新建画布",
    "home.existingCanvases": "已有画布",
    "home.existing": "已有画布",
    "canvas.workspace": "画布工作区",
    "canvas.active": "当前画布",
    "canvas.delete": "删除画布",
    "canvas.tools": "画布工具",
    "canvas.zoomOut": "缩小",
    "canvas.zoomIn": "放大",
    "common.create": "创建",
    "common.index": "目录",
    "common.chooseFile": "选择文件",
    "common.chooseImage": "选择图像",
    "common.choosePaper": "选择论文PDF",
    "common.noFile": "未选择文件",
    "common.read": "读取",
    "common.importPaper": "导入论文",
    "common.clear": "清除",
    "common.open": "打开",
    "common.delete": "删除",
    "common.close": "关闭",
    "common.run": "运行",
    "common.running": "生成中",
    "common.exportPdf": "导出PDF",
    "common.output": "输出",
    "common.inputText": "输入文本",
    "common.openFullText": "查看完整文本",
    "common.document": "文档",
    "common.semanticImage": "语义图像",
    "common.generatedImage": "生成的思辨图像",
    "nodes.text": "文本",
    "nodes.conversation": "对话",
    "nodes.upload": "上传",
    "nodes.image": "图像",
    "nodes.multimodal": "图文",
    "nodes.modify": "推演",
    "nodes.tool": "工具",
    "nodes.operation": "操作",
    "nodes.guidedScenario": "引导情境",
    "sidebar.create": "创建节点",
    "sidebar.textNode": "文本内容",
    "sidebar.conversationNode": "对话内容",
    "sidebar.uploadSource": "上传素材",
    "sidebar.imageNode": "图像节点",
    "sidebar.methodNode": "方法节点",
    "sidebar.operationNode": "操作节点",
    "sidebar.scenarioNode": "引导情境",
    "sidebar.startFlow": "开始引导流程",
    "workflow.start": "开始四种未来流程",
    "workflow.eyebrow": "引导式基础流程",
    "workflow.dialogTitle": "确立研究议题",
    "workflow.dialogIntro": "创建可编辑的研究简报和待运行的四种未来操作；此处不会调用模型、工具或图像生成。",
    "workflow.startMode": "起点类型",
    "workflow.modeResearch": "真实研究 / 研究者主导",
    "workflow.modeDesign": "设计设想 / 设计师主导",
    "workflow.topic": "研究议题",
    "workflow.topicPlaceholder": "这项研究想要探讨什么？",
    "workflow.focus": "研究关注点",
    "workflow.focusPlaceholder": "哪些证据、问题或前提需要被重新审视？",
    "workflow.assumptions": "默认假设",
    "workflow.stakeholders": "利益相关者",
    "workflow.tensions": "核心张力",
    "workflow.listPlaceholder": "每行填写一项",
    "workflow.create": "创建基础流程",
    "workflow.choose": "选择这条未来",
    "workflow.chosen": "已选，进入讨论",
    "workflow.awaitingSelection": "比较并选择一条未来",
    "workflow.inputManual": "使用信息卡片输入",
    "workflow.inputConversation": "或在下方对话框中描述",
    "workflow.inputReady": "信息卡片已经就绪；可在完整画布中直接编辑关联节点。",
    "workflow.undoStep": "撤销本步",
    "workflow.undoStepConfirm": "撤销当前流程步骤，并移除本步生成的卡片和节点吗？",
    "workflow.undoStepDone": "当前流程步骤已撤销。",
    "document.onlyPaperPdf": "导入论文只支持 PDF 文件。",
    "document.noReadableFile": "请先选择图像或论文 PDF。",
    "document.imageImported": "已将图片作为图像输入节点加入画布。",
    "document.paperImported": "已根据论文填入研究议题卡片。",
    "workflow.chooseOne": "从四个方向中仅选择一个",
    "workflow.toolsHint": "在左侧栏选择一个或多个工具，然后生成一条情境。",
    "workflow.scenarioReady": "当前情境已生成",
    "workflow.imageGenerating": "图片生成中",
    "workflow.imageFailed": "图片暂不可用",
    "workflow.expandText": "展开文本",
    "nodes.textTitle": "文本节点",
    "nodes.conversationTitle": "对话",
    "nodes.uploadTitle": "上传",
    "nodes.imageTitle": "图像节点",
    "nodes.multimodalTitle": "图文节点",
    "nodes.modifyTitle": "推演",
    "nodes.operationTitle": "操作节点",
    "nodes.textDefault": "新的文本信息节点。",
    "nodes.conversationDefault": "对话或中间思考内容。",
    "nodes.imageDefault": "图像语义摘要占位。",
    "nodes.operationDefault": "可配置的操作定义。",
    "output.text": "文本",
    "output.image": "图像",
    "output.multimodal": "图文",
    "status.idle": "空闲",
    "status.loading": "加载中",
    "status.ready": "就绪",
    "status.checking": "检查中",
    "status.configured": "已配置",
    "status.offline": "离线",
    "status.reading": "读取中",
    "status.importing": "导入中",
    "status.running": "生成中",
    "status.deleting": "删除中",
    "status.error": "错误",
    "status.draft": "草稿",
    "status.success": "完成",
    "status.failed": "失败",
    "status.stale": "待更新",
    "status.generated": "已生成",
    "status.orphaned": "已脱离原节点",
    "status.pending": "等待中",
    "status.active": "进行中",
    "status.succeeded": "已完成",
    "status.complete": "已完成",
    "autosave.saved": "已自动存储",
    "autosave.saving": "自动存储中...",
    "autosave.error": "存储失败",
    "export.title": "思辨共创工作台导出",
    "export.cards": "流程卡片",
    "export.canvasNodes": "画布节点",
    "export.chat": "聊天记录",
    "export.noMessages": "暂无聊天记录。",
    "export.generatedAt": "导出时间",
    "export.printHint": "在打印窗口中选择保存为 PDF。",
    "inspector.canvasSnapshot": "画布快照",
    "inspector.openCanvas": "打开一个画布以查看图谱状态。",
    "inspector.modelApi": "模型 API",
    "inspector.modelStatus": "模型服务状态将显示在这里。",
    "inspector.documentIntake": "文档读取",
    "inspector.documentPrompt": "上传 PDF、DOCX、TXT 或 MD 以查看提取结构。",
    "menu.nodeActions": "节点操作",
    "menu.deleteNode": "删除节点",
    "menu.deleteEdge": "删除连线",
    "reader.nodeText": "节点文本",
    "reader.generatedOutput": "生成结果",
    "reader.nodeImage": "节点图像",
    "reader.imagePreview": "图像预览",
    "reader.noText": "暂无文本内容。",
    "reader.imagePrompt": "图像提示词",
    "reader.semanticSummary": "语义描述",
    "reader.imageUrl": "图像地址",
    "reader.imageError": "图像错误",
    "project.nodes": "{count} 个节点",
    "project.renameHint": "双击重命名",
    "project.deleteLabel": "删除画布 {title}",
    "project.renamePrompt": "重命名画布",
    "project.untitled": "未命名画布",
    "project.deleteConfirm": "删除画布“{title}”及其全部节点、连线和运行记录？",
    "node.deleteConfirm": "删除节点“{title}”及其连接？",
    "node.imageFallback": "图像语义摘要占位。",
    "node.imageReference": "图像参考",
    "node.noImageUploaded": "尚未上传图像",
    "node.multimodalFallback": "图文输出占位。",
    "node.uploadPrompt": "上传 PDF、DOCX、TXT 或 MD。",
    "node.noFileUploaded": "尚未上传文件",
    "node.openImage": "打开图像预览",
    "node.inputPort": "输入端口",
    "node.outputPort": "输出端口",
    "node.revision": "版本 {count}",
    "generate.aria": "正在生成内容",
    "theme.dark": "深色",
    "theme.light": "浅色",
    "composition.parallel": "并行",
    "composition.sequential": "顺序",
    "composition.synthesis": "综合",
    "access.eyebrow": "私有 API 访问",
    "access.title": "输入你的 API Key",
    "access.label": "OpenAI API Key",
    "access.placeholder": "为当前标签页粘贴 API Key",
    "access.notice": "该 Key 仅保存在当前标签页的内存中，并且仅在运行模型操作时发送。刷新页面后会自动清除。",
    "access.continue": "继续",
    "access.invalid": "请输入有效的 API Key 后继续。",
    "access.required": "运行模型操作前，请先输入你的 API Key。",
    "access.active": "当前标签页已启用个人 API Key；网站不会保存该 Key。",
    "access.serverActive": "模型服务已就绪。",
    "conversation.eyebrow": "对话",
    "conversation.emptyTitle": "工作线程",
    "conversation.inputLabel": "添加对话内容",
    "conversation.placeholder": "为当前范围补充研究指令",
    "conversation.send": "发送",
    "conversation.scope": "当前范围",
    "conversation.policy.confirm": "确认后执行",
    "conversation.none": "当前范围暂无消息。",
    "conversation.history": "完整对话记录",
    "conversation.historyHint": "可滚动回顾完整对话。",
    "conversation.nodeEdited": "节点已直接修改",
    "conversation.nodeRemoved": "节点已直接移除",
    "conversation.branchInvalidated": "当前流程已移除此部分思辨",
    "conversation.superseded": "此部分思辨已不参与当前流程",
    "conversation.toolsChanged": "讨论方法已更新",
    "conversation.user": "研究者",
    "conversation.assistant": "助手",
    "conversation.system": "系统",
    "conversation.scientistInput": "科学家输入",
    "conversation.designerInput": "设计师输入",
    "conversation.startResearch": "从真实研究开始",
    "conversation.startDesign": "从设计设想开始",
    "conversation.perspectiveStart": "选择起点",
    "conversation.perspectiveInput": "本次输入",
    "conversation.quickPrefix": "快捷输入选项",
    "conversation.quickSelected": "已选",
    "conversation.quickConfirmHint": "可多选快捷输入，最后点击发送确认。",
    "conversation.quickLoading": "快捷输入加载中...",
    "conversation.generateScenario": "生成图文情境",
    "conversation.agentIntro": "AI 主持人：请描述一个研究条件或设计设想。我会继续追问谁在使用、谁受影响，以及哪里出现不确定。",
    "conversation.agentPrompt": "AI 主持人",
    "conversation.runWhatIf": "生成四条 What-if 线路",
    "workflow.card01": "研究议题",
    "workflow.card02": "关键词",
    "workflow.card03": "WHAT-IF",
    "workflow.card04": "小工具",
    "workflow.card05": "情境生成",
    "workflow.cardWaiting": "等待对话补全",
    "workflow.cardReady": "可复盘",
    "workflow.cardPending": "等待前序步骤",
    "workflow.initial01": "在下方选择「科学家输入」或「设计师输入」，再用一句话描述本轮材料。",
    "workflow.initial02": "智能体会把议题拆成关键词、默认假设和利益相关者三个分支。",
    "workflow.initial03": "确认关键词后，生成增长、崩溃、平衡、转变四条未来方向。",
    "workflow.initial04": "把工具应用到当前节点，并把分析结果回写到流程。",
    "workflow.initial05": "生成情境文本、图像材料与可导出的复盘逻辑。",
    "scope.eyebrow": "当前节点",
    "scope.loading": "正在载入范围",
    "scope.global": "全局图谱",
    "scope.returnLocal": "返回局部",
    "navigator.eyebrow": "总画布预览",
    "navigator.title": "总览",
    "navigator.openGlobal": "打开全局图谱",
    "navigator.openCanvas": "打开节点画布",
    "navigator.hint": "选择局部范围即可回到对应的局部图谱。",
    "navigator.scopes": "范围",
    "navigator.proposals": "命令提案",
    "navigator.none": "没有待处理提案。",
    "toolSidebar.eyebrow": "工具节点",
    "toolSidebar.title": "工具",
    "toolSidebar.none": "当前局部没有推演工具。",
    "toolSidebar.nodeType": "工具",
    "toolSidebar.selected": "已选",
    "toolSidebar.remove": "移除",
    "toolSidebar.toModify": "关联推演",
    "toolSidebar.required": "本轮讨论请选择至少一种方法。",
    "toolSidebar.recommended": "推荐",
    "modify.toolsInSidebar": "{count} 个工具节点在侧栏",
    "workflowStrip.eyebrow": "引导流程",
    "workflowStrip.brief": "研究简报",
    "workflowStrip.keywords": "关键词",
    "workflowStrip.whatIf": "What-if 方向",
    "workflowStrip.methods": "方法与工具",
    "workflowStrip.outcomes": "情景结果",
    "workflowStrip.ready": "就绪",
    "workflowStrip.active": "进行中",
    "workflowStrip.awaiting": "等待输入",
    "workflowStrip.empty": "当前没有可显示的流程阶段。",
    "stagePresentation.current": "当前环节",
    "stagePresentation.scope": "关联范围",
    "stagePresentation.methods": "已选方法",
    "stagePresentation.outputs": "已就绪结果",
    "stagePresentation.noMethods": "需要时，再从左侧选择方法。",
    "stagePresentation.moreMethods": "另有 {count} 项",
    "canvasFocus.eyebrow": "节点画布",
    "canvasFocus.close": "返回流程",
    "canvasFocus.zoomControls": "画布缩放控制",
    "operation.definition": "操作定义",
    "operation.toolsSelected": "{count} 个工具",
    "command.approve": "批准",
    "command.reject": "拒绝",
    "command.proposed": "待审核",
    "command.approved": "已批准",
    "command.rejected": "已拒绝",
    "command.applied": "已应用",
    "command.superseded": "已替代",
  },
};
let locale = localStorage.getItem(LOCALE_KEY) === "zh" ? "zh" : "en";

function t(key, values = {}) {
  const template = translations[locale]?.[key] || translations.en[key] || key;
  return template.replace(/\{(\w+)\}/g, (_, name) => String(values[name] ?? ""));
}

function setStatus(element, key) {
  element.textContent = t(`status.${key}`);
}

function setUiActionBusy(pending) {
  uiActionInFlight = Boolean(pending);
  document.documentElement.classList.toggle("ui-action-busy", uiActionInFlight);
  document
    .querySelectorAll("[data-quick-action], [data-guide-action], [data-guide-branch-id], [data-stage-branch-id], [data-conversation-perspective], [data-sidebar-tool-id]")
    .forEach((button) => {
      button.disabled = uiActionInFlight;
      button.setAttribute("aria-busy", String(uiActionInFlight));
    });
}

function isRevisionConflict(error) {
  return /revision conflict/i.test(String(error?.message || ""));
}

async function runUiAction(task) {
  if (uiActionInFlight) return;
  setUiActionBusy(true);
  setStatus(canvasStatus, "running");
  try {
    await task();
  } catch (error) {
    setStatus(canvasStatus, "error");
    canvasOutput.textContent = error.message;
    if (isRevisionConflict(error)) {
      await loadCanvas({ preserveView: false });
    }
  } finally {
    setUiActionBusy(false);
  }
}

function statusLabel(value) {
  const key = String(value || "draft").toLowerCase();
  return translations[locale]?.[`status.${key}`] ? t(`status.${key}`) : key;
}

function nodeTypeLabel(type) {
  return translations[locale]?.[`nodes.${type}`] ? t(`nodes.${type}`) : type;
}

function localizedToolCopy(tool, field) {
  const localCopy = locale === "zh" ? tool?.locales?.zh : null;
  const localized = localCopy?.[field];
  if (localized) return String(localized);
  return String(tool?.[field] || tool?.id || "");
}

function toolAssetUrl(tool) {
  const asset = tool?.presentation?.asset;
  const toolId = String(tool?.id || "").trim();
  const assetPath = String(asset?.path || "").trim();
  if (!toolId || asset?.kind !== "package-relative" || !assetPath) return "";
  const safePath = assetPath.split("/").filter(Boolean).map((part) => encodeURIComponent(part)).join("/");
  return safePath ? `/tool-assets/${encodeURIComponent(toolId)}/${safePath}` : "";
}

function localizedOperationCopy(definition, field) {
  const localCopy = locale === "zh" ? definition?.locales?.zh : null;
  const localized = localCopy?.[field];
  if (localized) return String(localized);
  return String(definition?.[field] || "");
}

function localizedOperationUiCopy(definition, field) {
  const localCopy = locale === "zh" ? definition?.locales?.zh?.ui : null;
  const localized = localCopy?.[field];
  if (localized) return String(localized);
  return String(definition?.ui?.[field] || "");
}

function localizedControlPolicy(policy) {
  const value = String(policy || "confirm");
  return translations[locale]?.[`conversation.policy.${value}`] || value;
}

function toolById(toolId) {
  for (const node of activeCanvas?.nodes || []) {
    const tool = (node.config?.tools || []).find((item) => item.id === toolId);
    if (tool) return tool;
  }
  return null;
}

function localizedReferenceTitle(title) {
  if (locale !== "zh") return title;
  const labels = {
    "Research brief": "研究简报",
    "Keywords to confirm": "待确认关键词",
    "Guided Scenario": "引导情境",
    "Discussion tools": "讨论工具",
    "Growth": "增长",
    "Collapse": "崩塌",
    "Discipline": "平衡",
    "Transformation": "转变",
    "Growth scenario": "增长情境",
    "Collapse scenario": "崩塌情境",
    "Discipline scenario": "平衡情境",
    "Transformation scenario": "转变情境",
    "Text Output": "文本输出",
    "Image Output": "图像输出",
    "Text+Image Output": "文本与图像输出",
    "Four Futures research thread": "四种未来研究线程",
    "Working thread": "工作线程",
    "Global graph": "全局图谱",
    "Research material": "研究材料",
    "Current inquiry": "当前议题",
    "Artifact branch": "产物分支",
    "Start inquiry": "开始议题",
    "Compare four What-if futures": "比较四条假设情境",
    "Four Futures foundation": "四种未来基础流程",
    "Frame the inquiry": "确定研究议题",
    "Confirm keywords": "确认关键词",
    "Input cards": "信息输入",
    "Four What-if futures": "四个 What-if",
    "Choose tools": "选择工具",
    "Generate scenario": "生成情境",
    "Generate four What-if futures": "生成四条假设情境",
    "Choose one future": "选择一条未来",
    "Discuss the chosen future": "讨论已选未来",
    "Text Node": "文本节点",
    "Conversation": "对话节点",
    "Upload Source": "上传来源",
    "Image Node": "图像节点",
    "Method Node": "方法节点",
    "Operation Node": "操作节点",
    "Semantic Image": "语义图像",
    "Guided process": "引导流程",
  };
  return labels[title] || title;
}

function localizedWorkflowScopeLabel(scope, fallback = "") {
  const nodeIds = new Set(scope?.selector?.node_ids || []);
  const branchNode = (activeCanvas?.nodes || []).find((node) =>
    nodeIds.has(node.id) && node.payload?.scenario_branch,
  );
  const strategy = branchNode?.payload?.scenario_branch?.strategy_label || "";
  if (strategy) {
    const localizedStrategy = localizedReferenceTitle(strategy);
    return locale === "zh" ? `${localizedStrategy}情境` : `${localizedStrategy} scenario`;
  }
  return localizedReferenceTitle(scope?.label || fallback);
}

function localizedConversationBody(body) {
  if (locale !== "zh") return body;
  const copy = {
    "What should this inquiry focus on? You can write a short answer, skip it, or edit the Research brief node directly.": "这项研究应聚焦什么？你可以简短回答、跳过，或直接编辑“研究简报”节点。",
    "The research brief and keyword scaffold are ready. Review either node if needed, then run Guided Scenario to compare four What-if futures.": "研究简报和关键词框架已就绪。需要时可检查这两个节点，然后运行“引导情境”来比较四条假设情境。",
    "What assumptions currently shape this topic? Add one per line or sentence; you can also skip.": "目前有哪些默认假设正在塑造这个议题？每行或每句写一项，也可以跳过。",
    "Who is affected, involved, or able to act? Add stakeholders or skip.": "谁会受到影响、参与其中或有能力行动？请补充利益相关者，也可以跳过。",
    "What is the central tension or trade-off? Add one or more, or skip.": "核心张力或权衡是什么？请补充一项或多项，也可以跳过。",
    "Keywords are confirmed. The four What-if stage is ready; run the Guided Scenario node when you want to generate the four directions.": "关键词已确认。现在可以运行“引导情境”节点，生成四条假设情境方向。",
    "The input cards are complete. The four What-if stage is ready; run the Guided Scenario node to generate growth, collapse, balance, and transformation directions.": "信息卡片已完成。现在直接进入 What-if 阶段，可以运行“引导情境”生成增长、崩溃、平衡、转变四条方向。",
    "Start from a real research inquiry.": "从一个真实研究问题开始。",
    "Start from a design proposition.": "从一个设计命题开始。",
    "This conversation writes to the canonical research nodes. You can also edit those nodes directly; both routes update the same workflow record.": "这段对话会写入规范研究节点。你也可以直接编辑节点；两种方式都会更新同一条流程记录。",
    "Four What-if futures are ready. Compare their assumptions and tensions, then choose one branch before beginning discussion.": "四条假设情境已生成。请比较它们的默认假设与张力，再选择一个方向开始讨论。",
    "Generated four What-if futures from the current canonical inputs.": "已根据当前规范输入生成四条假设情境。",
    "The input cards are complete. You can edit the linked nodes directly, or run Guided Scenario to compare four What-if futures.": "信息卡片已完成。你可以直接编辑关联节点，或运行“引导情境”比较四个 What-if。",
    "Imported the paper PDF into the research inquiry cards. The first-step brief is filled from the paper and ready for What-if generation.": "已将论文 PDF 导入研究议题卡片。第一步内容已根据论文自动补全，可以继续生成 What-if。",
    "Current workflow step was undone. Start again by choosing a perspective and entering a research topic.": "当前流程步骤已撤销。请选择输入视角，并重新输入研究议题。",
    "Selected a What-if branch and prepared its discussion tools.": "已选择一条假设情境方向，并准备好相应的讨论工具。",
    "Ran Discussion tools and added a new output node.": "已运行讨论工具，并新增一个输出节点。",
    "Generated the current scenario from the selected tools.": "已根据所选工具生成当前情境。",
    "A different What-if branch is now the only active line of this workflow.": "已切换 What-if 分支；流程中仅保留该分支为当前有效线。",
    "A later tool run replaced this scenario on the current workflow line.": "后一次工具运行已替代当前流程线中的这条情境。",
    "A What-if branch was edited directly. Re-run the comparison before using a selected branch.": "一条假设情境已被直接修改。使用已选方向前，请重新运行比较。",
    "A workflow input changed. Its generated futures are now stale.": "流程输入已改变；此前生成的未来方向现已失效。",
    "Connected two nodes.": "已连接两个节点。",
    "Removed a connection between two nodes.": "已移除两个节点之间的连接。",
    "The inquiry frame is complete. Review the editable keyword node, then confirm the keywords here to unlock the four What-if stage.": "研究框架已完成。系统会直接进入四条 What-if 阶段；你仍可回看并编辑关键词节点。",
    "Updated Discussion tools.": "讨论工具已更新。",
    "Added Guided Scenario.": "已添加引导情境。",
  };
  if (copy[body]) return copy[body];
  const selectedMethods = body.match(/^Updated discussion tools: (\d+) method\(s\) selected\.$/);
  if (selectedMethods) return `讨论工具已更新：已选择 ${selectedMethods[1]} 个方法。`;
  const operationOutput = body.match(/^Ran (.+) and added (\d+) output nodes\.$/);
  if (operationOutput) return `已运行${localizedReferenceTitle(operationOutput[1])}，并新增 ${operationOutput[2]} 个输出节点。`;
  const singleOutput = body.match(/^Ran (.+) and added a new output node\.$/);
  if (singleOutput) return `已运行${localizedReferenceTitle(singleOutput[1])}，并新增一个输出节点。`;
  const addedNode = body.match(/^Added (.+)\.$/);
  if (addedNode) return `已添加${localizedReferenceTitle(addedNode[1])}。`;
  const updatedNode = body.match(/^Updated (.+)\.$/);
  if (updatedNode) return `已更新${localizedReferenceTitle(updatedNode[1])}。`;
  const deletedNode = body.match(/^Deleted (.+)\.$/);
  if (deletedNode) return `已删除${localizedReferenceTitle(deletedNode[1])}。`;
  return body;
}

function applyLocale(nextLocale) {
  locale = nextLocale === "zh" ? "zh" : "en";
  document.documentElement.lang = locale === "zh" ? "zh-CN" : "en";
  document.title = t("document.title");
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    element.textContent = t(element.dataset.i18n);
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((element) => {
    element.placeholder = t(element.dataset.i18nPlaceholder);
  });
  document.querySelectorAll("[data-i18n-aria-label]").forEach((element) => {
    element.setAttribute("aria-label", t(element.dataset.i18nAriaLabel));
  });
  document.querySelectorAll("[data-i18n-title]").forEach((element) => {
    element.setAttribute("title", t(element.dataset.i18nTitle));
  });
  document.querySelectorAll("[data-language-toggle]").forEach((button) => {
    const targetLanguage = locale === "zh" ? "EN" : "中文";
    button.textContent = targetLanguage;
    button.setAttribute("aria-label", locale === "zh" ? "Switch to English" : "切换至中文");
  });
  localStorage.setItem(LOCALE_KEY, locale);
  applyTheme(document.documentElement.dataset.theme || "light");
  if (activeProject) {
    updateCanvasTitle(activeProject.title);
    renderInteraction();
    renderCanvas();
  }
  loadProjects().catch((error) => {
    projectsEl.textContent = error.message;
  });
}

async function requestJson(url, options = {}) {
  const { requiresApiKey = false, headers: optionHeaders = {}, ...requestOptions } = options;
  const method = String(requestOptions.method || "GET").toUpperCase();
  const isMutating = !["GET", "HEAD"].includes(method);
  if (isMutating) setAutoSaveState("saving");
  const headers = requestOptions.body instanceof FormData ? { ...optionHeaders } : {
    "Content-Type": "application/json",
    ...optionHeaders,
  };
  if (requiresApiKey && tabApiKey) {
    headers["X-Speculative-Web-Api-Key"] = tabApiKey;
  }
  const response = await fetch(url, {
    ...requestOptions,
    headers,
  });
  const payload = await response.json();
  if (!response.ok) {
    if (isMutating) setAutoSaveState("error");
    throw new Error(payload.error || `Request failed: ${response.status}`);
  }
  if (isMutating) setAutoSaveState("saved");
  return payload;
}

function setAutoSaveState(state) {
  if (!autosaveStatus) return;
  const key = state === "saving" ? "autosave.saving" : (state === "error" ? "autosave.error" : "autosave.saved");
  autosaveStatus.textContent = t(key);
  autosaveStatus.dataset.state = state;
  window.clearTimeout(autosaveStatusTimer);
  if (state === "saving") return;
  autosaveStatusTimer = window.setTimeout(() => {
    autosaveStatus.textContent = t("autosave.saved");
    autosaveStatus.dataset.state = "saved";
  }, 1800);
}

function scheduleViewportAutosave() {
  if (!activeProject || !activeCanvas) return;
  window.clearTimeout(autosaveTimer);
  autosaveTimer = window.setTimeout(saveViewportState, 650);
}

async function saveViewportState() {
  if (!activeProject || !activeCanvas) return;
  const viewport = {
    x: Math.max(0, Math.round(workspace.scrollLeft)),
    y: Math.max(0, Math.round(workspace.scrollTop)),
    zoom,
  };
  activeCanvas.viewport = viewport;
  try {
    await requestJson(`/api/projects/${activeProject.id}/canvas`, {
      method: "PATCH",
      body: JSON.stringify({ viewport }),
    });
  } catch (error) {
    setStatus(canvasStatus, "error");
    canvasOutput.textContent = error.message;
  }
}

function withExpectedRevision(payload) {
  const revision = activeInteraction?.revision ?? activeCanvas?.revision;
  return Number.isInteger(revision) ? { ...payload, expected_revision: revision } : payload;
}

function requireTabApiKey() {
  if (tabApiKey || hasServerModelAccess()) return true;
  apiAccessError.textContent = t("access.required");
  setApiAccessState(true);
  apiAccessKey.focus();
  return false;
}

function hasServerModelAccess() {
  return modelAccess.openaiRunsEnabled && modelAccess.openaiApiKeyConfigured && !modelAccess.userApiKeyRequired;
}

function setApiAccessState(isOpen) {
  apiAccessGate.classList.toggle("hidden", !isOpen);
  appShell.inert = isOpen;
  appShell.setAttribute("aria-hidden", String(isOpen));
}

function acceptTabApiKey(event) {
  event.preventDefault();
  const candidate = apiAccessKey.value.trim();
  if (candidate.length < 20 || /\s/.test(candidate)) {
    apiAccessError.textContent = t("access.invalid");
    apiAccessKey.focus();
    return;
  }
  tabApiKey = candidate;
  apiAccessKey.value = "";
  apiAccessError.textContent = "";
  setApiAccessState(false);
  if (activeProject) loadModelStatus().catch(() => {});
}

async function loadProjects() {
  const { projects } = await requestJson("/api/projects");
  projectCount.textContent = String(projects.length);
  projectsEl.innerHTML = "";
  for (const project of projects) {
    const entry = document.createElement("article");
    entry.className = "project-entry";
    const button = document.createElement("button");
    button.className = "project-item";
    button.type = "button";
    button.innerHTML = `
      <strong>${escapeHtml(project.title)}</strong>
      <span>${escapeHtml(project.updated_at)}</span>
      <span>${t("project.nodes", { count: project.node_count || 0 })} · ${escapeHtml(statusLabel(project.status))}</span>
      <small>${t("project.renameHint")}</small>
    `;
    button.addEventListener("click", () => openCanvas(project));
    button.addEventListener("dblclick", (event) => {
      event.stopPropagation();
      renameProject(project);
    });
    const deleteButton = document.createElement("button");
    deleteButton.className = "project-delete";
    deleteButton.type = "button";
    deleteButton.textContent = t("common.delete");
    deleteButton.setAttribute("aria-label", t("project.deleteLabel", { title: project.title }));
    deleteButton.addEventListener("click", (event) => {
      event.stopPropagation();
      deleteProject(project);
    });
    entry.append(button, deleteButton);
    projectsEl.append(entry);
  }
}

async function openCanvas(project) {
  activeProject = project;
  activeInteraction = null;
  activeProjection = null;
  activeSessionId = null;
  activeScopeId = null;
  previewFocusedStageId = "";
  updateCanvasTitle(project.title);
  home.classList.add("hidden");
  canvas.classList.add("active");
  await loadCanvas({ preserveView: false });
  await loadModelStatus();
}

function updateCanvasTitle(title) {
  canvasTitle.textContent = title;
  canvasTitle.title = t("project.renameHint");
}

async function loadCanvas({ preserveView = true, consistencyRetry = 0, autoStartBranchImages = false } = {}) {
  if (!activeProject) return;
  const previousCanvasId = activeCanvas?.id;
  const previousZoom = zoom;
  const previousView = captureCanvasView();
  closeNodeMenu();
  setStatus(canvasStatus, "loading");
  const { canvas: graph } = await requestJson(`/api/projects/${activeProject.id}/canvas`);
  const shouldPreserveView = preserveView && previousCanvasId === graph.id;
  activeCanvas = graph;
  zoom = shouldPreserveView ? clampZoom(previousZoom) : clampZoom(activeCanvas.viewport?.zoom ?? 1);
  const interaction = await loadInteraction({ preserveScope: shouldPreserveView });
  if (interaction?.revision !== graph.revision && consistencyRetry < 1) {
    return loadCanvas({ preserveView: shouldPreserveView, consistencyRetry: consistencyRetry + 1, autoStartBranchImages });
  }
  setStatus(canvasStatus, "ready");
  canvasOutput.textContent = JSON.stringify(summarizeCanvas(graph), null, 2);
  renderCanvas();
  if (shouldPreserveView) restoreCanvasView(previousView);
  else restoreCanvasView({
    scrollLeft: Number(activeCanvas.viewport?.x || 0),
    scrollTop: Number(activeCanvas.viewport?.y || 0),
  });
  if (autoStartBranchImages) queuePendingBranchImages();
}

async function loadInteraction({ preserveScope = true } = {}) {
  if (!activeProject) return;
  const { interaction } = await requestJson(`/api/projects/${activeProject.id}/interaction`);
  activeInteraction = interaction;
  const sessions = interaction.conversation_sessions || [];
  const workflows = interaction.workflow_instances || [];
  const scopedWorkflow = preserveScope && activeScopeId
    ? workflows.find((workflow) => workflowScopeIds(workflow).includes(activeScopeId))
    : null;
  const scopedSession = scopedWorkflow
    ? sessions.find((session) => session.id === scopedWorkflow.session_id || session.workflow_instance_id === scopedWorkflow.id)
    : null;
  const currentSession = sessions.find((session) => session.id === activeSessionId);
  const focusedSession = sessions.find((session) => session.active_scope_id && session.active_scope_id !== "scope-global");
  const currentMatchesScope = !preserveScope
    || !activeScopeId
    || currentSession?.active_scope_id === activeScopeId
    || (scopedWorkflow && (currentSession?.workflow_instance_id === scopedWorkflow.id || currentSession?.guide?.workflow_instance_id === scopedWorkflow.id));
  const session = (currentMatchesScope ? currentSession : null)
    || scopedSession
    || currentSession
    || focusedSession
    || sessions[0]
    || null;
  activeSessionId = session?.id || null;
  const availableScopeIds = new Set((interaction.scopes || []).map((scope) => scope.id));
  const linkedWorkflow = workflows.find((workflow) =>
    workflow.session_id === session?.id || workflow.id === session?.workflow_instance_id,
  );
  const mustFollowSessionScope = session?.guide?.stage_id === "stale" || linkedWorkflow?.status === "stale";
  const preferredScope = !mustFollowSessionScope && preserveScope && availableScopeIds.has(activeScopeId)
    ? activeScopeId
    : (session?.active_scope_id || "scope-global");
  await loadScopeProjection(preferredScope, { render: false, fit: !preserveScope });
  renderInteraction();
  return interaction;
}

async function loadScopeProjection(scopeId, { render = true, fit = true } = {}) {
  if (!activeProject) return;
  const { projection } = await requestJson(`/api/projects/${activeProject.id}/scopes/${scopeId}/projection`);
  activeScopeId = projection.scope.id;
  activeProjection = projection;
  if (fit) zoom = fittedScopeZoom(projection);
  if (render) {
    renderInteraction();
    renderCanvas();
  }
}

function fittedScopeZoom(projection) {
  const nodes = projection?.nodes || [];
  if (!nodes.length) return 1;
  const maxRight = Math.max(...nodes.map((node) => Number(node.position?.x || 0) + Number(node.size?.width || 240)), 320) + 72;
  const maxBottom = Math.max(...nodes.map((node) => Number(node.position?.y || 0) + Number(node.size?.height || 170)), 260) + 72;
  const availableWidth = Math.max(280, workspace.clientWidth - 18);
  const availableHeight = Math.max(260, workspace.clientHeight - 18);
  return clampZoom(Math.min(1, availableWidth / maxRight, availableHeight / maxBottom));
}

function displayGraph() {
  // The graph surface has one canonical source: the complete canvas. Scopes guide
  // conversation and stage cards, but they must never turn the node canvas into a
  // partial copy where upstream nodes, outputs, or images disappear.
  return activeCanvas || activeProjection || { nodes: [], edges: [] };
}

function activeSession() {
  return (activeInteraction?.conversation_sessions || []).find((session) => session.id === activeSessionId) || null;
}

function activeWorkflow() {
  const session = activeSession();
  const workflows = activeInteraction?.workflow_instances || [];
  return workflows.find((workflow) => workflow.session_id === session?.id)
    || workflows.find((workflow) => workflow.id === session?.workflow_instance_id)
    || workflows.find((workflow) => workflowScopeIds(workflow).includes(activeScopeId))
    || workflows.find((workflow) => workflow.status && workflow.status !== "stale")
    || null;
}

function workflowScopeIds(workflow) {
  if (!workflow) return [];
  return [
    workflow.foundation_scope_id,
    workflow.comparison_scope_id,
    ...Object.values(workflow.branch_scope_ids || {}),
  ].filter(Boolean);
}

function workflowForBranch(nodeId) {
  return (activeInteraction?.workflow_instances || []).find((workflow) =>
    Array.isArray(workflow.branch_node_ids) && workflow.branch_node_ids.includes(nodeId),
  ) || null;
}

function defaultLocalScopeId() {
  const sessionScopeId = activeSession()?.active_scope_id;
  if (sessionScopeId && sessionScopeId !== "scope-global") return sessionScopeId;
  return (activeInteraction?.scopes || []).find((scope) => scope.id !== "scope-global")?.id || "scope-global";
}

function captureCanvasView() {
  return {
    scrollLeft: workspace.scrollLeft,
    scrollTop: workspace.scrollTop,
  };
}

function restoreCanvasView(view) {
  requestAnimationFrame(() => {
    workspace.scrollLeft = view.scrollLeft;
    workspace.scrollTop = view.scrollTop;
  });
}

async function loadModelStatus() {
  setStatus(modelStatus, "checking");
  const { model } = await requestJson("/api/model/status");
  modelAccess = {
    openaiApiKeyConfigured: Boolean(model.openai_api_key_configured),
    openaiRunsEnabled: Boolean(model.openai_runs_enabled),
    userApiKeyRequired: Boolean(model.user_api_key_required),
  };
  if (tabApiKey || hasServerModelAccess()) {
    setStatus(modelStatus, "ready");
    modelOutput.textContent = tabApiKey ? t("access.active") : t("access.serverActive");
    return;
  }
  setStatus(modelStatus, model.openai_api_key_configured ? "configured" : "offline");
  modelOutput.textContent = JSON.stringify(model, null, 2);
}

function renderCanvas() {
  const graph = displayGraph();
  if (!graph) return;
  nodesLayer.innerHTML = "";
  for (const node of graph.nodes || []) {
    nodesLayer.append(renderNode(node));
  }
  requestAnimationFrame(() => {
    renderPlane();
    renderCanvasPreview();
  });
}

function renderConversationPerspective(session) {
  const isStartChoice = session?.guide?.stage_id === "start" && !session?.guide?.workflow_instance_id;
  const guideMode = session?.guide?.start_mode;
  if (isStartChoice && (guideMode === "research" || guideMode === "design")) {
    conversationPerspective = guideMode;
  }
  const labels = isStartChoice
    ? { research: t("conversation.startResearch"), design: t("conversation.startDesign") }
    : { research: t("conversation.scientistInput"), design: t("conversation.designerInput") };
  const groupLabel = isStartChoice ? t("conversation.perspectiveStart") : t("conversation.perspectiveInput");
  conversationPerspectiveButtons.forEach((button) => {
    const perspective = button.dataset.conversationPerspective === "design" ? "design" : "research";
    const selected = perspective === conversationPerspective;
    button.textContent = labels[perspective];
    button.classList.toggle("active", selected);
    button.setAttribute("aria-pressed", String(selected));
  });
  const group = conversationPerspectiveButtons[0]?.closest(".conversation-perspective");
  if (group) {
    group.dataset.modeLabel = groupLabel;
    group.classList.toggle("is-start-choice", Boolean(isStartChoice));
  }
}

function renderInteraction() {
  const interaction = activeInteraction;
  const session = activeSession();
  const scope = activeProjection?.scope || (interaction?.scopes || []).find((item) => item.id === activeScopeId);
  conversationTitle.textContent = localizedReferenceTitle(session?.title || t("conversation.emptyTitle"));
  conversationPolicy.textContent = localizedControlPolicy(session?.control_policy);
  scopeViewTitle.textContent = localizedReferenceTitle(scope?.label || t("scope.loading"));
  conversationScopeIndicator.textContent = scope?.label ? `${t("conversation.scope")}: ${localizedReferenceTitle(scope.label)}` : "";
  canvasFocusTitle.textContent = localizedReferenceTitle(scope?.label || t("scope.loading"));
  scopeNodeCount.textContent = `${scope?.node_count ?? activeProjection?.nodes?.length ?? 0}`;
  navigatorRevision.textContent = `r${interaction?.revision ?? activeCanvas?.revision ?? 0}`;
  const isGlobalScope = activeScopeId === "scope-global";
  const isEntry = session?.guide?.stage_id === "start" && !session?.guide?.workflow_instance_id;
  returnLocalScope.classList.toggle("hidden", !isGlobalScope || Boolean(isEntry));
  conversationDock?.classList.toggle("is-entry", Boolean(isEntry));
  workspaceMain?.classList.toggle("is-entry", Boolean(isEntry));
  renderConversationPerspective(session);

  const progress = session?.progress || [];
  conversationProgress.hidden = Boolean(isEntry) || progress.length < 2;
  conversationProgress.innerHTML = progress.map((step) => `
    <button class="progress-step ${escapeHtml(step.status || "pending")} ${previewFocusedStageId === step.workflow_stage_id ? "is-focused" : ""}" type="button" data-progress-scope="${escapeHtml(step.scope_id)}">
      <span>${escapeHtml(step.label)}</span><span>${escapeHtml(statusLabel(step.status || "pending"))}</span>
    </button>
  `).join("");
  conversationProgress.querySelectorAll("[data-progress-scope]").forEach((button) => {
    button.addEventListener("click", () => setActiveScope(button.dataset.progressScope));
  });

  const messages = (session?.messages || []).filter((message) =>
    !(message.role === "system" && message.kind !== "activity"),
  );
  renderConversationHistory(session, messages, isEntry);

  renderConversationGuide(session);

  const scopes = interaction?.scopes || [];
  scopeList.innerHTML = scopes.map((item) => `
    <button class="scope-row ${item.id === activeScopeId ? "active" : ""}" type="button" data-scope-id="${escapeHtml(item.id)}">
      <span>${escapeHtml(item.label)}</span><span>${escapeHtml(item.node_count)}</span>
    </button>
  `).join("");
  scopeList.querySelectorAll("[data-scope-id]").forEach((button) => {
    button.addEventListener("click", () => setActiveScope(button.dataset.scopeId));
  });

  renderWorkflowStrip(session);
  renderCommandProposals();
  renderToolSidebar();
}

function renderConversationHistory(session, messages, isEntry) {
  const sessionId = session?.id || "";
  const previous = conversationHistoryState.get(sessionId);
  const messageIds = messages.map((message) => message.id).filter(Boolean);
  const addedMessage = Boolean(previous && messageIds.some((messageId) => !previous.messageIds.includes(messageId)));
  if (sessionId) {
    conversationHistoryState.set(sessionId, {
      messageIds: previous?.messageIds || [],
      scrollTop: conversationMessages.scrollTop,
      atBottom: conversationMessages.scrollHeight - conversationMessages.scrollTop - conversationMessages.clientHeight < 24,
    });
  }
  const previewMessages = messages.slice(-2);
  const emptyText = isEntry ? t("conversation.agentIntro") : t("conversation.none");
  conversationMessages.innerHTML = messages.length
    ? `<div class="conversation-history-preview" role="button" tabindex="0" aria-label="${escapeHtml(locale === "zh" ? "打开完整对话记录" : "Open full conversation history")}">
        <div class="conversation-history-preview-copy">${previewMessages.map((message) => renderConversationMessage(message)).join("")}</div>
        <span class="conversation-history-preview-hint">${escapeHtml(locale === "zh" ? "悬停预览 · 点击查看全部记录" : "Preview · Click to view history")}</span>
      </div>`
    : `<p class="empty-panel">${escapeHtml(emptyText)}</p>`;
  if (conversationHistoryDialogMessages) {
    conversationHistoryDialogMessages.innerHTML = messages.length
      ? messages.map((message) => renderConversationMessage(message)).join("")
      : `<p class="empty-panel">${escapeHtml(emptyText)}</p>`;
  }
  conversationMessages.querySelector(".conversation-history-preview")?.addEventListener("click", openConversationHistory);
  conversationMessages.querySelector(".conversation-history-preview")?.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      openConversationHistory();
    }
  });
  requestAnimationFrame(() => {
    if (!sessionId) return;
    const history = conversationHistoryState.get(sessionId) || previous;
    if (!previous || (addedMessage && history?.atBottom)) {
      conversationMessages.scrollTop = conversationMessages.scrollHeight;
    } else if (history) {
      conversationMessages.scrollTop = Math.min(history.scrollTop, conversationMessages.scrollHeight);
    }
    conversationHistoryState.set(sessionId, {
      messageIds,
      scrollTop: conversationMessages.scrollTop,
      atBottom: conversationMessages.scrollHeight - conversationMessages.scrollTop - conversationMessages.clientHeight < 24,
    });
  });
}

function openConversationHistory() {
  if (!conversationHistoryDialog?.showModal) return;
  conversationHistoryDialog.showModal();
  requestAnimationFrame(() => {
    if (conversationHistoryDialogMessages) {
      conversationHistoryDialogMessages.scrollTop = conversationHistoryDialogMessages.scrollHeight;
    }
    conversationHistoryClose?.focus();
  });
}

conversationHistoryClose?.addEventListener("click", () => conversationHistoryDialog?.close());
conversationHistoryDialog?.addEventListener("click", (event) => {
  if (event.target === conversationHistoryDialog) conversationHistoryDialog.close();
});

conversationMessages.addEventListener("scroll", () => {
  const sessionId = activeSession()?.id || "";
  if (!sessionId) return;
  const previous = conversationHistoryState.get(sessionId) || { messageIds: [] };
  conversationHistoryState.set(sessionId, {
    ...previous,
    scrollTop: conversationMessages.scrollTop,
    atBottom: conversationMessages.scrollHeight - conversationMessages.scrollTop - conversationMessages.clientHeight < 24,
  });
});

function renderConversationMessage(message) {
  const messageState = message.state === "removed" ? "removed" : (message.state === "superseded" ? "superseded" : "active");
  const meta = conversationMessageMeta(message, messageState);
  const perspectiveLabel = message.role === "user" && message.input_perspective
    ? t(message.input_perspective === "design" ? "conversation.designerInput" : "conversation.scientistInput")
    : "";
  const refs = message.related_node_refs?.length
    ? message.related_node_refs
    : (message.related_node_ids || []).map((nodeId) => ({ id: nodeId, title: findNode(nodeId)?.title || nodeId }));
  return `
    <article class="conversation-message ${escapeHtml(message.role)} ${escapeHtml(message.kind || "message")} is-${messageState}">
      <span class="message-role">${escapeHtml(t(`conversation.${message.role}`))}${perspectiveLabel ? `<em>${escapeHtml(perspectiveLabel)}</em>` : ""}</span>
      <p>${escapeHtml(message.role === "user" ? message.body : compactConversationText(localizedConversationBody(message.body)))}</p>
      ${meta ? `<small class="message-activity-state">${escapeHtml(meta)}</small>` : ""}
      ${refs.length ? `<small class="message-node-refs">${escapeHtml(refs.map((ref) => localizedReferenceTitle(ref.title || ref.id)).join(" · "))}</small>` : ""}
    </article>
  `;
}

function conversationMessageMeta(message, state) {
  if (state === "removed") return t("conversation.branchInvalidated");
  if (state === "superseded") return t("conversation.superseded");
  const activityType = message.activity?.type || "";
  if (activityType === "workflow.invalidated") return t("conversation.branchInvalidated");
  if (activityType === "node.deleted") return t("conversation.nodeRemoved");
  if (activityType === "node.updated") return t("conversation.nodeEdited");
  if (activityType === "workflow.discussion_tools_changed") return t("conversation.toolsChanged");
  return "";
}

function renderWorkflowStrip(session) {
  if (!workflowStrip && !stagePresentation) return;
  const stages = workflowStages(session);
  renderStagePresentation(stages);
  if (!workflowStrip) return;
  // Stage navigation now lives in the same four-card deck as stage content.
  // Keep this legacy element empty so the visual layer cannot create a second,
  // divergent workflow representation below the cards.
  workflowStrip.hidden = true;
  workflowStrip.innerHTML = "";
}

function workflowStages(session) {
  const workflow = activeWorkflow();
  const progress = session?.progress || [];
  if (!progress.length) {
    return [{
      label: t("workflowStrip.brief"),
      state: t("workflowStrip.awaiting"),
      scopeId: activeScopeId || "scope-global",
      active: true,
    }];
  }
  return progress.map((step) => ({
    id: step.workflow_stage_id || "",
    label: localizedWorkflowStageLabel(workflow, step),
    state: statusLabel(step.status || "pending"),
    scopeId: step.scope_id || activeScopeId || "scope-global",
    active: previewFocusedStageId ? step.workflow_stage_id === previewFocusedStageId : step.status === "active",
  }));
}

function localizedWorkflowStageLabel(workflow, step) {
  const stageId = step?.workflow_stage_id || "";
  const localCopy = locale === "zh" ? workflow?.definition_snapshot?.locales?.zh?.stages?.[stageId] : null;
  return String(localCopy?.label || localizedReferenceTitle(step?.label || stageId || t("workflowStrip.brief")));
}

function activeStageTools() {
  const scopedNodes = activeProjection?.nodes || [];
  const scopedModifyNodes = scopedNodes.filter((node) => node.type === "modify");
  const sourceNodes = scopedModifyNodes.length
    ? scopedModifyNodes
    : (activeCanvas?.nodes || []).filter((node) => node.type === "modify");
  const uniqueTools = new Map();
  sourceNodes.forEach((node) => {
    (node.config?.tools || []).filter((tool) => tool.enabled !== false && tool.selected).forEach((tool) => {
      const key = tool.id || tool.label;
      if (!key || uniqueTools.has(key)) return;
      uniqueTools.set(key, tool);
    });
  });
  return [...uniqueTools.values()];
}

function renderStagePresentation(stages) {
  if (!stagePresentation) return;
  const workflow = activeWorkflow();
  if (!workflow) {
    renderFoundationEntryCard();
    return;
  }
  if (!stages.length) {
    stagePresentation.innerHTML = "";
    return;
  }
  const tools = activeStageTools();
  const visibleTools = tools.slice(0, 3);
  const focusedStage = stages.find((stage) => previewFocusedStageId && stage.id === previewFocusedStageId)
    || stages.find((stage) => stage.scopeId === activeScopeId)
    || stages.find((stage) => stage.active)
    || stages[0];
  const methodCards = visibleTools.length
    ? visibleTools.map((tool) => {
      const presentation = tool.presentation || {};
      const assetUrl = toolAssetUrl(tool);
      return `
        <article class="stage-tool-card ${assetUrl ? "has-graphic" : ""}" data-card-kind="${escapeHtml(presentation.card_kind || "tool")}" data-icon-token="${escapeHtml(presentation.icon_token || tool.id || "tool")}" data-accent-token="${escapeHtml(presentation.accent_token || "neutral")}">
          ${assetUrl
    ? `<img class="stage-tool-asset" src="${escapeHtml(assetUrl)}" alt="" aria-hidden="true" />`
    : `<span class="stage-tool-glyph" aria-hidden="true"><i></i><i></i><i></i></span>`}
          <span class="stage-tool-copy"><strong>${escapeHtml(localizedToolCopy(tool, "label"))}</strong><small>${escapeHtml(presentation.card_kind || t("stagePresentation.methods"))}</small></span>
        </article>
      `;
    }).join("")
    : `<p class="stage-empty-state">${escapeHtml(t("stagePresentation.noMethods"))}</p>`;
  const stageBody = (stage) => {
    if (stage.id === "input") return renderStageInputCards(workflow, stage);
    if (stage.id === "four_futures") return renderStageBranchChoices(workflow, stage);
    if (stage.id === "tools") return `<section class="stage-card-track" aria-label="${escapeHtml(t("stagePresentation.methods"))}">
      ${methodCards}
      ${tools.length > visibleTools.length ? `<span class="stage-track-more">${escapeHtml(t("stagePresentation.moreMethods", { count: tools.length - visibleTools.length }))}</span>` : ""}
    </section>
    <p class="stage-card-note">${escapeHtml(t("workflow.toolsHint"))}</p>`;
    if (stage.id === "scenario") return renderStageOutputCards();
    return `<p class="stage-card-note">${escapeHtml(stage.state)}</p>`;
  };
  stagePresentation.innerHTML = `<div class="stage-deck" aria-label="${escapeHtml(t("stagePresentation.current"))}">
    ${stages.map((stage, index) => {
      const scope = (activeInteraction?.scopes || []).find((item) => item.id === stage.scopeId);
      const isCurrent = stage === focusedStage;
      return `<section class="stage-deck-card ${isCurrent ? "is-current" : ""}" data-stage-id="${escapeHtml(stage.id)}">
        <button class="stage-deck-header" type="button" data-stage-scope="${escapeHtml(stage.scopeId)}" aria-pressed="${isCurrent ? "true" : "false"}">
          <span class="stage-index">${String(index + 1).padStart(2, "0")}</span>
          <span class="stage-deck-heading"><strong>${escapeHtml(stage.label)}</strong><small>${escapeHtml(stage.state)}</small></span>
          ${isCurrent ? `<span class="stage-current-marker">${escapeHtml(t("stagePresentation.current"))}</span>` : ""}
        </button>
        <div class="stage-deck-body">
          ${stageBody(stage)}
        </div>
        <footer class="stage-deck-footer"><span>${escapeHtml(t("stagePresentation.scope"))}</span><strong>${escapeHtml(localizedWorkflowScopeLabel(scope, stage.label))}</strong></footer>
      </section>`;
    }).join("")}
  </div>`;
  stagePresentation.querySelectorAll("[data-stage-branch-id]").forEach((button) => {
    button.addEventListener("click", () => runUiAction(() => selectWorkflowBranch(button.dataset.stageWorkflowId, button.dataset.stageBranchId)));
  });
  stagePresentation.querySelectorAll("[data-stage-scope]").forEach((button) => {
    button.addEventListener("click", () => setActiveScope(button.dataset.stageScope));
  });
  stagePresentation.querySelectorAll("[data-open-foundation-input]").forEach((button) => {
    button.addEventListener("click", openFoundationWorkflowDialog);
  });
}

function renderFoundationEntryCard() {
  const cards = [
    {
      index: "01",
      title: t("workflow.card01"),
      state: t("workflow.cardWaiting"),
      body: t("workflow.initial01"),
      fields: [t("workflow.topic"), t("workflow.focus"), t("workflow.assumptions"), t("workflow.stakeholders"), t("workflow.tensions")],
      current: true,
    },
    {
      index: "02",
      title: t("workflow.card02"),
      state: t("workflow.cardPending"),
      body: t("workflow.initial02"),
      fields: [locale === "zh" ? "关键词提取" : "Keyword extraction", t("workflow.assumptions"), t("workflow.stakeholders")],
    },
    {
      index: "03",
      title: t("workflow.card03"),
      state: t("workflow.cardPending"),
      body: t("workflow.initial03"),
      fields: [locale === "zh" ? "增长" : "Growth", locale === "zh" ? "崩溃" : "Collapse", locale === "zh" ? "平衡" : "Balance", locale === "zh" ? "转变" : "Transformation"],
    },
    {
      index: "04",
      title: t("workflow.card04"),
      state: t("workflow.cardPending"),
      body: t("workflow.initial04"),
      fields: [locale === "zh" ? "警示故事" : "Cautionary tales", locale === "zh" ? "未来锥" : "Futures cone", locale === "zh" ? "影响轮" : "Futures wheel", locale === "zh" ? "体验阶梯" : "Experience ladder"],
    },
    {
      index: "05",
      title: t("workflow.card05"),
      state: t("workflow.cardPending"),
      body: t("workflow.initial05"),
      fields: [locale === "zh" ? "情境文本" : "Scenario text", locale === "zh" ? "图像材料" : "Image material", locale === "zh" ? "逻辑关系" : "Logic map", locale === "zh" ? "导出" : "Export"],
    },
  ];
  stagePresentation.innerHTML = `<section class="foundation-start-deck" aria-label="${escapeHtml(t("workflow.eyebrow"))}">
    ${cards.map((card) => `<article class="foundation-start-card ${card.current ? "is-current" : ""}">
      <header>
        <span class="stage-index">${escapeHtml(card.index)}</span>
        <div>
          <strong>${escapeHtml(card.title)}</strong>
          <small>${escapeHtml(card.state)}</small>
        </div>
      </header>
      <p>${escapeHtml(card.body)}</p>
      <div class="foundation-start-fields">
        ${card.fields.map((field) => `<span>${escapeHtml(field)}</span>`).join("")}
      </div>
    </article>`).join("")}
  </section>`;
}

function renderStageInputCards(workflow, activeStage) {
  if (activeStage?.id !== "input") return "";
  const briefNode = (activeCanvas?.nodes || []).find((node) => node.id === workflow?.source_node_ids?.[0]);
  const brief = briefNode?.payload?.workflow_brief;
  if (!brief) {
    return `<section class="stage-input-cards stage-input-empty">
      <strong>${escapeHtml(t("workflow.inputManual"))}</strong>
      <span>${escapeHtml(t("workflow.inputConversation"))}</span>
      <button type="button" data-open-foundation-input>${escapeHtml(t("workflow.inputManual"))}</button>
    </section>`;
  }
  const fields = [
    [t("workflow.topic"), brief.topic],
    [t("workflow.focus"), brief.research_focus],
    [t("workflow.assumptions"), Array.isArray(brief.assumptions) ? brief.assumptions.join(" · ") : ""],
    [t("workflow.stakeholders"), Array.isArray(brief.stakeholders) ? brief.stakeholders.join(" · ") : ""],
    [t("workflow.tensions"), Array.isArray(brief.tensions) ? brief.tensions.join(" · ") : ""],
  ].filter(([, value]) => String(value || "").trim());
  return `<section class="stage-input-cards" aria-label="${escapeHtml(t("workflow.inputManual"))}">
    ${fields.map(([label, value]) => `<article class="stage-input-field"><small>${escapeHtml(label)}</small><strong>${escapeHtml(value)}</strong></article>`).join("")}
    <p>${escapeHtml(t("workflow.inputReady"))}</p>
  </section>`;
}

function renderStageBranchChoices(workflow, activeStage) {
  if (activeStage?.id !== "four_futures" || !workflow?.branch_node_ids?.length) return `<p class="stage-card-note">${escapeHtml(t("workflowStrip.awaiting"))}</p>`;
  const selectable = workflow.status === "awaiting_selection";
  return `<section class="stage-branch-choices" aria-label="${escapeHtml(t("workflow.chooseOne"))}">
    <header><strong>${escapeHtml(selectable ? t("workflow.chooseOne") : activeStage.state)}</strong><small>${escapeHtml(t("conversation.quickConfirmHint"))}</small></header>
    <div class="stage-card-track">${workflow.branch_node_ids.map((nodeId) => {
      const node = findNode(nodeId);
      const branch = node?.payload?.scenario_branch || {};
      const selected = nodeId === workflow.selected_branch_node_id;
      const tag = "article";
      const action = "";
      const premise = branch.future_premise || branch.what_if || "";
      const actors = Array.isArray(branch.key_actors) ? branch.key_actors.slice(0, 3).join(" · ") : "";
      const imageUrl = branch.image_url || node?.payload?.image_url || "";
      const imageStatus = branch.image_status || node?.payload?.image_status || "";
      const imageError = branch.image_error || node?.payload?.image_error || "";
      return `<${tag} class="stage-branch-card ${selected ? "is-selected" : ""}" data-branch-strategy="${escapeHtml(branch.strategy || "")}"${action}>
        ${imageUrl
    ? `<img class="stage-branch-image" src="${escapeHtml(imageUrl)}" alt="${escapeHtml(branch.visual_brief || branch.what_if || "")}" loading="lazy" />`
    : `<span class="stage-branch-visual ${imageStatus === "failed" ? "is-failed" : "is-generating"}" aria-hidden="true"><i></i><b></b><em></em><strong>${escapeHtml(imageStatus === "failed" || imageError ? t("workflow.imageFailed") : t("workflow.imageGenerating"))}</strong></span>`}
        <strong>${escapeHtml(localizedReferenceTitle(branch.strategy_label || node?.title || t("workflow.choose")))}</strong>
        <details class="stage-branch-copy">
          <summary>${escapeHtml(localizedReferenceTitle(branch.what_if || ""))}<span>${escapeHtml(t("workflow.expandText"))}</span></summary>
          <small>${escapeHtml(premise)}</small>
          <span class="stage-branch-meta">${escapeHtml(actors || branch.core_tension || "")}</span>
          <span class="stage-branch-visual-brief">${escapeHtml(branch.visual_brief || "")}</span>
        </details>
      </${tag}>`;
    }).join("")}</div>
  </section>`;
}

function renderStageOutputCards() {
  const outputs = (activeCanvas?.nodes || []).filter((node) =>
    node.payload?.requested_output_type || node.payload?.model_output || node.payload?.image_url,
  );
  if (!outputs.length) return `<p class="stage-card-note">${escapeHtml(t("workflow.scenarioReady"))}</p>`;
  return `<section class="stage-card-track" aria-label="${escapeHtml(t("stagePresentation.outputs"))}">
    ${outputs.map((node) => `<article class="stage-output-card ${node.status === "stale" ? "is-stale" : ""}">
      ${node.payload?.image_url ? `<img class="stage-output-image" src="${escapeHtml(node.payload.image_url)}" alt="${escapeHtml(node.payload?.semantic_summary || node.title || "")}" loading="lazy" />` : ""}
      <small>${escapeHtml(statusLabel(node.status || "pending"))}</small>
      <strong>${escapeHtml(localizedReferenceTitle(node.title || t("workflowStrip.outcomes")))}</strong>
      <span>${escapeHtml(node.payload?.semantic_summary || node.payload?.text || node.payload?.model_output || "")}</span>
      ${node.payload?.image_error ? `<small class="stage-output-error">${escapeHtml(node.payload.image_error)}</small>` : ""}
    </article>`).join("")}
  </section>`;
}

function activeWorkflowBrief(workflow) {
  const sourceId = workflow?.source_node_ids?.[0];
  const node = (activeCanvas?.nodes || []).find((item) => item.id === sourceId);
  return node?.payload?.workflow_brief || {};
}

function quickButton(label, body, action = "answer") {
  return { label, body, action };
}

function quickSelectionKey(session = activeSession()) {
  const guide = session?.guide || {};
  return [
    session?.id || "session",
    guide.stage_id || "message",
    guide.pending_field || "",
    guide.workflow_instance_id || session?.workflow_instance_id || "",
  ].join("::");
}

function selectedQuickInputs(session = activeSession()) {
  return [...(quickInputSelections.get(quickSelectionKey(session)) || new Map()).values()];
}

function clearQuickInputs(session = activeSession()) {
  quickInputSelections.delete(quickSelectionKey(session));
  if (conversationInput) conversationInput.value = "";
}

function syncQuickInputsToComposer(session = activeSession()) {
  if (!conversationInput) return;
  const selected = selectedQuickInputs(session);
  conversationInput.value = selected.map((option) => option.body && !["select_branch", "tool_select"].includes(option.action) ? option.body : option.label).filter(Boolean).join("\n");
}

function toggleQuickInputSelection(option) {
  const session = activeSession();
  if (!session || !option?.label) return;
  const key = quickSelectionKey(session);
  const selected = new Map(quickInputSelections.get(key) || []);
  const id = `${option.action || "answer"}::${option.body || option.label}`;
  if (selected.has(id)) {
    selected.delete(id);
  } else {
    if (option.action === "select_branch" || option.action === "run_four_futures" || option.action === "run_scenario" || option.action === "confirm_keywords") {
      selected.clear();
    }
    selected.set(id, option);
  }
  if (selected.size) quickInputSelections.set(key, selected);
  else quickInputSelections.delete(key);
  syncQuickInputsToComposer(session);
}

function localizedQuickOptions(stage, guide, workflow) {
  const zh = locale === "zh";
  const brief = activeWorkflowBrief(workflow);
  const topic = String(brief.topic || (zh ? "这个议题" : "this issue"));
  const mode = guide?.start_mode || conversationPerspective;
  const materialLabel = zh
    ? (mode === "design" ? "设计设想" : "真实研究")
    : (mode === "design" ? "design proposition" : "research condition");
  if (stage === "start") {
    return [
      quickButton(zh ? "从使用现场开始" : "Start from a use scene", zh ? `一个${materialLabel}进入具体使用现场，使用者、受影响者和不确定边界需要被同时讨论。` : `A ${materialLabel} enters a concrete use scene where users, affected people, and uncertain boundaries must be discussed.`, "begin"),
      quickButton(zh ? "从研究背景开始" : "Start from background", zh ? `这个${materialLabel}的背景来自一组真实条件、限制边界和可争议的应用语境。` : `This ${materialLabel} begins from real conditions, limits, and a debatable application context.`, "begin"),
      quickButton(zh ? "从争议点开始" : "Start from a tension", zh ? `这个议题最值得讨论的是技术承诺、实际使用和影响承担者之间的张力。` : `The key issue is the tension between technical promise, real use, and those who carry the impact.`, "begin"),
      quickButton(zh ? "从 What-if 开始" : "Start with What-if", zh ? `如果这个条件成为未来现场里的默认设置，会怎样？` : `What if this condition became a default setting in a future context?`, "begin"),
      quickButton(zh ? "从反例开始" : "Start from a counterexample", zh ? `一个可能推翻默认设想的反例进入现场，使原本稳定的判断变得不确定。` : `A counterexample enters the scene and makes a previously stable assumption uncertain.`, "begin"),
    ];
  }
  if (stage === "frame_focus") {
    return [
      quickButton(zh ? "补充研究背景" : "Add research background", zh ? `${topic} 的研究关注是技术机制、使用现场和可验证边界之间的关系。` : `${topic} focuses on the relation between mechanism, use context, and verifiable limits.`),
      quickButton(zh ? "换个角度追问" : "Ask from another angle", zh ? `把 ${topic} 放进一个未来现场，先追问谁在使用、谁被影响、哪里失控。` : `Place ${topic} in a future scene, then ask who uses it, who is affected, and where it becomes unstable.`),
      quickButton(zh ? "加入反例" : "Add a counterexample", zh ? `反例：${topic} 并不总是提升效率，它也可能制造新的解释负担。` : `Counterexample: ${topic} may not always improve efficiency; it may create a new burden of explanation.`),
    ];
  }
  if (stage === "frame_assumptions") {
    return [
      quickButton(zh ? "生成争议点" : "Generate tensions", zh ? `更多数据会带来更好判断\n使用者会接受系统建议\n风险可以通过流程控制` : `More data produces better judgment\nUsers will accept system suggestions\nRisk can be controlled through process`),
      quickButton(zh ? "加入反例" : "Add a counterexample", zh ? `材料或系统在真实环境中表现不稳定\n被影响者可能拒绝参与\n专家判断和自动判断发生冲突` : `The material or system may behave unpredictably in real settings\nAffected people may refuse to participate\nExpert judgment may conflict with automated judgment`),
    ];
  }
  if (stage === "frame_stakeholders") {
    return [
      quickButton(zh ? "提取利益相关者" : "Extract stakeholders", zh ? `直接使用者\n研究人员\n操作人员\n被间接影响的人\n监管或伦理审查者` : `Direct users\nResearchers\nOperators\nIndirectly affected people\nRegulators or ethics reviewers`),
      quickButton(zh ? "换个角度追问" : "Ask from another angle", zh ? `谁拥有解释权？谁承担后果？谁可以拒绝这个系统？` : `Who has the right to interpret it? Who carries the consequences? Who can refuse the system?`),
    ];
  }
  if (stage === "frame_tensions") {
    return [
      quickButton(zh ? "生成争议点" : "Generate tensions", zh ? `效率提升与解释权之间的张力\n技术稳定性与真实使用复杂度之间的张力\n研究可控性与公共影响之间的张力` : `Efficiency versus interpretive agency\nTechnical stability versus real-use complexity\nResearch control versus public impact`),
      quickButton(zh ? "把它变成 What-if" : "Turn it into What-if", zh ? `如果 ${topic} 成为公共流程中的默认条件，会怎样？` : `What if ${topic} became a default condition in a public process?`),
      quickButton(zh ? "加入反例" : "Add a counterexample", zh ? `一个关键角色拒绝使用后，系统如何解释失败？` : `If one key actor refuses to use it, how does the system explain failure?`),
    ];
  }
  if (stage === "keywords") {
    return [
      quickButton(zh ? "把它变成 What-if" : "Turn it into What-if", "", "confirm_keywords"),
    ];
  }
  if (stage === "four_futures" && !workflow?.branch_node_ids?.length) {
    return [
      quickButton(zh ? "把它变成 What-if" : "Turn it into What-if", "", "run_four_futures"),
    ];
  }
  if (stage === "four_futures" && workflow?.branch_node_ids?.length) {
    return workflow.branch_node_ids.map((nodeId) => {
      const node = findNode(nodeId);
      const branch = node?.payload?.scenario_branch || {};
      const label = localizedReferenceTitle(branch.strategy_label || node?.title || (zh ? "未来方向" : "Future direction"));
      const whatIf = localizedReferenceTitle(branch.what_if || "");
      return quickButton(whatIf ? `${label}：${whatIf}` : label, nodeId, "select_branch");
    });
  }
  if (stage === "tools") {
    const discussion = findNode(workflow?.discussion_node_id);
    const tools = (discussion?.config?.tools || []).filter((tool) => tool.enabled !== false);
    const policy = discussion?.config?.selection_policy || {};
    const recommendedIds = new Set(Array.isArray(policy.recommended_tool_ids) ? policy.recommended_tool_ids : []);
    const selectedCount = tools.filter((tool) => tool.selected).length;
    const toolOptions = tools
      .map((tool) => {
        const label = localizedToolCopy(tool, "label");
        return {
          ...quickButton(recommendedIds.has(tool.id) ? `${t("toolSidebar.recommended")}：${label}` : label, tool.id, "tool_select"),
          recommended: recommendedIds.has(tool.id),
        };
      })
      .sort((a, b) => Number(Boolean(b.recommended)) - Number(Boolean(a.recommended)));
    return selectedCount
      ? [...toolOptions, quickButton(t("conversation.generateScenario"), "", "run_scenario")]
      : toolOptions;
  }
  return [
    quickButton(zh ? "换个角度追问" : "Ask from another angle", zh ? `围绕 ${topic} 重新追问角色、依据和不确定性。` : `Revisit roles, evidence, and uncertainty around ${topic}.`, "answer"),
    quickButton(zh ? "加入反例" : "Add a counterexample", zh ? `一个反例或边界情况会改变 ${topic} 的默认判断。` : `A counterexample or boundary case changes the default judgment around ${topic}.`, "answer"),
  ];
}

function renderQuickOptionsLoading() {
  return `<div class="quick-input-options is-loading">
    <button type="button" disabled aria-busy="true">${escapeHtml(t("conversation.quickLoading"))}</button>
    <small class="quick-confirm-hint">${escapeHtml(t("conversation.quickLoading"))}</small>
  </div>`;
}

function renderQuickOptions(options) {
  const selected = new Set(selectedQuickInputs().map((option) => `${option.action || "answer"}::${option.body || option.label}`));
  return `<div class="quick-input-options">
    ${options.map((option) => {
    const id = `${option.action || "answer"}::${option.body || option.label}`;
    const isSelected = selected.has(id);
    return `<button type="button" class="${isSelected ? "is-selected" : ""}" data-quick-action="${escapeHtml(option.action)}" data-quick-body="${escapeHtml(option.body)}" data-quick-label="${escapeHtml(option.label)}" aria-pressed="${isSelected ? "true" : "false"}" aria-label="${escapeHtml(`${t("conversation.quickPrefix")}: ${option.label}`)}">${isSelected ? `<span class="quick-selected-mark">${escapeHtml(t("conversation.quickSelected"))}</span>` : ""}${escapeHtml(option.label)}</button>`;
  }).join("")}
    <small class="quick-confirm-hint">${escapeHtml(t("conversation.quickConfirmHint"))}</small>
  </div>`;
}

function agentGuideRequestKey(session, stage, workflow) {
  const brief = compactBriefForAgent(activeWorkflowBrief(workflow));
  const messageSignature = (session?.messages || []).slice(-4).map((message) =>
    `${message.id || message.created_at || ""}:${message.role}:${compactConversationText(message.body || "", 80)}`,
  );
  return JSON.stringify({
    project: activeProject?.id || "",
    session: session?.id || "",
    stage,
    pending: session?.guide?.pending_field || "",
    workflow: workflow?.id || "",
    locale,
    workflow_status: workflow?.status || "",
    branch_ids: workflow?.branch_node_ids || [],
    selected_branch: workflow?.selected_branch_node_id || "",
    brief,
    messageSignature,
  });
}

function agentGuidePayload(session, stage, workflow) {
  const guide = session?.guide || {};
  const brief = compactBriefForAgent(activeWorkflowBrief(workflow));
  const branchTitles = (workflow?.branch_node_ids || []).map((nodeId) => {
    const node = findNode(nodeId);
    const branch = node?.payload?.scenario_branch || {};
    return compactConversationText(localizedReferenceTitle(branch.strategy_label || branch.what_if || node?.title || ""), 160);
  }).filter(Boolean);
  return {
    stage,
    pending_field: guide.pending_field || "",
    start_mode: guide.start_mode || conversationPerspective,
    input_perspective: conversationPerspective,
    locale,
    brief,
    topic: brief.topic || "",
    workflow_status: workflow?.status || "",
    has_branches: Boolean(workflow?.branch_node_ids?.length),
    branch_titles: branchTitles.slice(0, 4),
    selected_branch: compactConversationText(localizedReferenceTitle(findNode(workflow?.selected_branch_node_id)?.title || ""), 160),
    history: (session?.messages || [])
      .filter((message) => message.kind !== "activity")
      .slice(-4)
      .map((message) => ({
      role: message.role,
      body: compactConversationText(message.body || "", 220),
      kind: message.kind,
      input_perspective: message.input_perspective || "",
    })),
  };
}

function agentOptionAction(stage, option) {
  const text = String(option || "");
  if (stage === "start") return "begin";
  if (["frame_focus", "frame_assumptions", "frame_stakeholders", "frame_tensions"].includes(stage)) return "answer";
  if (stage === "keywords") {
    return "confirm_keywords";
  }
  if (stage === "four_futures") {
    return "run_four_futures";
  }
  return "answer";
}

function agentQuickOptions(stage, fallbackOptions, agentGuide, workflow) {
  if ((stage === "four_futures" && workflow?.branch_node_ids?.length) || stage === "tools") {
    return fallbackOptions;
  }
  const options = Array.isArray(agentGuide?.options) ? agentGuide.options.filter(Boolean).slice(0, 5) : [];
  if (!options.length) return fallbackOptions;
  return options.map((option) => {
    const label = String(option).trim();
    const action = agentOptionAction(stage, label);
    return quickButton(label, action === "begin" || action === "answer" ? label : "", action);
  });
}

function requestAgentGuide(session, stage, workflow, key) {
  if (!activeProject || !session?.id || agentGuideCache.has(key) || agentGuideInFlight.has(key)) return;
  agentGuideInFlight.add(key);
  requestJson(`/api/projects/${activeProject.id}/conversations/${session.id}/agent-guide`, {
    method: "POST",
    body: JSON.stringify(agentGuidePayload(session, stage, workflow)),
    requiresApiKey: true,
  }).then((payload) => {
    rememberAgentGuide(key, payload);
  }).catch((error) => {
    rememberAgentGuide(key, { usedFallback: true, error: error.message });
  }).finally(() => {
    agentGuideInFlight.delete(key);
    const currentSession = activeSession();
    if (currentSession?.id === session.id) renderConversationGuide(currentSession);
  });
}

function renderConversationGuide(session) {
  if (!conversationGuideActions) return;
  const guide = session?.guide;
  if (!guide || guide.status !== "active") {
    conversationGuideActions.innerHTML = "";
    return;
  }
  const workflow = (activeInteraction?.workflow_instances || []).find((item) => item.id === guide.workflow_instance_id);
  const stage = guide.stage_id || "start";
  const localized = locale === "zh";
  const fallbackOptions = localizedQuickOptions(stage, guide, workflow);
  const agentKey = agentGuideRequestKey(session, stage, workflow);
  const liveGuide = agentGuideCache.get(agentKey);
  const agentLoading = agentGuideInFlight.has(agentKey) || !agentGuideCache.has(agentKey);
  const quickOptions = agentQuickOptions(stage, fallbackOptions, liveGuide, workflow);
  const liveQuestion = liveGuide?.question ? String(liveGuide.question) : "";
  const liveHint = liveGuide?.hint ? String(liveGuide.hint) : "";
  const loadingHint = agentLoading ? (localized ? "AI 正在根据当前材料生成追问..." : "AI is generating a contextual prompt...") : "";
  const quickMarkup = agentLoading && !liveGuide ? renderQuickOptionsLoading() : renderQuickOptions(quickOptions);
  requestAgentGuide(session, stage, workflow, agentKey);
  if (stage === "start") {
    conversationGuideActions.innerHTML = `
      <span>${escapeHtml(liveQuestion || (localized ? "当前步骤：研究议题。先选择从真实研究还是设计设想开始，再描述一个可讨论的起点。" : "Current step: research issue. Choose whether to start from research or a design proposition, then describe a discussable starting point."))}</span>
      ${liveHint || loadingHint ? `<small class="agent-guide-hint">${escapeHtml(liveHint || loadingHint)}</small>` : ""}
      ${quickMarkup}
    `;
  } else if (["frame_focus", "frame_assumptions", "frame_stakeholders", "frame_tensions"].includes(stage)) {
    conversationGuideActions.innerHTML = `
      <span>${escapeHtml(liveQuestion || (localized ? "AI 主持人正在推动补充：" : "The AI host is prompting the next detail:"))}</span>
      ${liveHint || loadingHint ? `<small class="agent-guide-hint">${escapeHtml(liveHint || loadingHint)}</small>` : ""}
      ${quickMarkup}
      <button class="quiet-guide-action" type="button" data-guide-action="skip">${localized ? "跳过这一步" : "Skip this step"}</button>
    `;
  } else if (stage === "keywords") {
    conversationGuideActions.innerHTML = `
      <span>${escapeHtml(liveQuestion || (localized ? "关键词、默认假设和利益相关者已汇合；确认后进入 What-if。" : "Keywords, assumptions, and stakeholders have converged; confirm to enter What-if."))}</span>
      ${liveHint || loadingHint ? `<small class="agent-guide-hint">${escapeHtml(liveHint || loadingHint)}</small>` : ""}
      ${quickMarkup}
    `;
  } else if (stage === "four_futures" && workflow?.branch_node_ids?.length && workflow?.status === "awaiting_selection") {
    conversationGuideActions.innerHTML = `
      <span>${escapeHtml(liveQuestion || (localized ? "从四个方向中选择一条继续展开：" : "Choose one of the four directions to continue:"))}</span>
      ${liveHint || loadingHint ? `<small class="agent-guide-hint">${escapeHtml(liveHint || loadingHint)}</small>` : ""}
      ${quickMarkup}
    `;
  } else if (stage === "four_futures") {
    conversationGuideActions.innerHTML = `
      <span>${escapeHtml(liveQuestion || (localized ? "下一步：生成增长、崩溃、平衡、转变四条 What-if 线路。" : "Next: generate growth, collapse, balance, and transformation What-if lines."))}</span>
      ${liveHint || loadingHint ? `<small class="agent-guide-hint">${escapeHtml(liveHint || loadingHint)}</small>` : ""}
      ${quickMarkup}
    `;
  } else if (stage === "tools") {
    conversationGuideActions.innerHTML = `
      <span>${escapeHtml(liveQuestion || (localized ? "选择一个或多个工具介入当前情境线，再按发送确认。" : "Choose one or more tools for the current scenario line, then press Send."))}</span>
      ${liveHint || loadingHint ? `<small class="agent-guide-hint">${escapeHtml(liveHint || loadingHint)}</small>` : ""}
      ${quickMarkup}
    `;
  } else if (stage === "choose_future" && workflow?.branch_node_ids?.length) {
    // Legacy workflow snapshots retain their historical guide identifier.
    conversationGuideActions.innerHTML = `
      <span>${escapeHtml(liveQuestion || (localized ? "选择一个方向进入讨论：" : "Choose a direction to discuss:"))}</span>
      ${liveHint || loadingHint ? `<small class="agent-guide-hint">${escapeHtml(liveHint || loadingHint)}</small>` : ""}
      ${workflow.branch_node_ids.map((nodeId) => `<button type="button" data-guide-branch-id="${escapeHtml(nodeId)}" data-guide-workflow-id="${escapeHtml(workflow.id)}">${escapeHtml(localizedReferenceTitle(findNode(nodeId)?.title || (localized ? "未来方向" : "Future direction")))}</button>`).join("")}
    `;
  } else if (stage === "stale") {
    conversationGuideActions.innerHTML = `<span>${localized ? "关联节点已改变。旧分支已失效；修复输入边后可直接重新运行该节点。" : "A linked node changed. Existing branches are stale; restore the inputs, then run the node again."}</span>`;
  } else {
    conversationGuideActions.innerHTML = "";
  }
  conversationGuideActions.querySelectorAll("[data-guide-start-mode]").forEach((button) => {
    button.addEventListener("click", () => runUiAction(() => advanceConversationGuide({ action: "set_start_mode", start_mode: button.dataset.guideStartMode })));
  });
  conversationGuideActions.querySelectorAll("[data-guide-action]").forEach((button) => {
    button.addEventListener("click", () => runUiAction(() => advanceConversationGuide({ action: button.dataset.guideAction })));
  });
  conversationGuideActions.querySelectorAll("[data-guide-branch-id]").forEach((button) => {
    button.addEventListener("click", () => runUiAction(() => selectWorkflowBranch(button.dataset.guideWorkflowId, button.dataset.guideBranchId)));
  });
  conversationGuideActions.querySelectorAll("[data-quick-action]").forEach((button) => {
    button.addEventListener("click", () => handleQuickInput(button.dataset.quickAction, button.dataset.quickBody, button.dataset.quickLabel));
  });
  if (uiActionInFlight) setUiActionBusy(true);
}

function renderToolSidebar() {
  const nodes = activeProjection?.nodes || [];
  const modifyNodes = nodes.filter((node) => node.type === "modify");
  if (!modifyNodes.length) {
    toolSidebarList.innerHTML = `<p class="empty-panel">${escapeHtml(t("toolSidebar.none"))}</p>`;
    return;
  }
  toolSidebarList.innerHTML = modifyNodes.map((node) => {
    const tools = (node.config?.tools || []).filter((tool) => tool.enabled !== false);
    const policy = node.config?.selection_policy || {};
    const minimumSelected = Math.max(0, Number(policy.minimum_selected) || 0);
    const selectedCount = tools.filter((tool) => tool.selected).length;
    const recommendedIds = new Set(Array.isArray(policy.recommended_tool_ids) ? policy.recommended_tool_ids : []);
    return `
      <section class="tool-sidebar-group">
        ${minimumSelected > selectedCount ? `<p class="tool-sidebar-policy">${escapeHtml(t("toolSidebar.required"))}</p>` : ""}
        ${tools.map((tool) => {
          const assetUrl = toolAssetUrl(tool);
          const toolLabel = localizedToolCopy(tool, "label");
          const toolDescription = localizedToolCopy(tool, "description");
          return `
          <button
            class="tool-sidebar-row ${tool.selected ? "selected" : ""} ${recommendedIds.has(tool.id) ? "recommended" : ""}"
            type="button"
            data-sidebar-modify-id="${escapeHtml(node.id)}"
            data-sidebar-tool-id="${escapeHtml(tool.id)}"
            data-card-kind="${escapeHtml(tool.presentation?.card_kind || "tool")}"
            title="${escapeHtml(toolLabel)}"
            aria-label="${escapeHtml(toolDescription ? `${toolLabel}: ${toolDescription}` : toolLabel)}"
          >${assetUrl
    ? `<img class="tool-sidebar-asset" src="${escapeHtml(assetUrl)}" alt="" aria-hidden="true" />`
    : `<span class="tool-card-mark" aria-hidden="true"></span>`}${recommendedIds.has(tool.id) ? `<small>${escapeHtml(t("toolSidebar.recommended"))}</small>` : ""}</button>
        `;
        }).join("")}
      </section>
    `;
  }).join("");
  toolSidebarList.querySelectorAll("[data-sidebar-tool-id]").forEach((button) => {
    button.addEventListener("click", () => runUiAction(async () => {
      const modifyNode = activeCanvas?.nodes.find((node) => node.id === button.dataset.sidebarModifyId);
      if (!modifyNode) return;
      const tool = (modifyNode.config?.tools || []).find((item) => item.id === button.dataset.sidebarToolId);
      await setToolSelection(modifyNode, button.dataset.sidebarToolId, !tool?.selected);
    }));
  });
  if (uiActionInFlight) setUiActionBusy(true);
}

function renderCanvasPreview() {
  if (!canvasPreviewViewport || !canvasPreviewPlane) return;
  const graphNodes = activeCanvas?.nodes || [];
  const workflow = activeWorkflow();
  const nodesById = new Map(graphNodes.map((node) => [node.id, node]));
  const workflowLayers = workflow
    ? [
      (workflow.source_node_ids || []).filter((id) => nodesById.has(id)),
      [workflow.keyword_node_id].filter((id) => nodesById.has(id)),
      [workflow.operation_node_id].filter((id) => nodesById.has(id)),
      (workflow.branch_node_ids || []).filter((id) => nodesById.has(id)),
      [workflow.selected_branch_node_id].filter((id) => nodesById.has(id)),
      [workflow.discussion_node_id].filter((id) => nodesById.has(id)),
      [workflow.active_scenario_node_id].filter((id) => nodesById.has(id)),
    ].filter((layer) => layer.length)
    : previewTreeLayers(graphNodes, activeCanvas?.edges || []);
  const workflowIds = new Set(workflowLayers.flat());
  const overflowNodes = graphNodes.filter((node) => !workflowIds.has(node.id));
  const layers = [
    ...workflowLayers,
    ...previewTreeLayers(overflowNodes, activeCanvas?.edges || []),
  ].filter((layer) => layer.length);
  const visibleIds = [...new Set(layers.flat())];
  const points = new Map();
  layers.forEach((layer, index) => {
    layer.forEach((nodeId, itemIndex) => {
      points.set(nodeId, {
        x: 18 + ((itemIndex + 1) * 64) / (layer.length + 1),
        y: 12 + ((index + 1) * 76) / (layers.length + 1),
      });
    });
  });
  const edges = (activeCanvas?.edges || []).filter((edge) => visibleIds.includes(edge.source_node_id) && visibleIds.includes(edge.target_node_id));
  const selectedId = workflow?.selected_branch_node_id || "";
  const activeOutputId = workflow?.active_scenario_node_id || "";
  canvasPreviewPlane.style.width = "100%";
  canvasPreviewPlane.style.height = "100%";
  canvasPreviewPlane.style.transform = "none";
  canvasPreviewPlane.innerHTML = `<svg class="workflow-tree-preview" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet" role="img" aria-label="${escapeHtml(t("navigator.title"))}">
    ${edges.map((edge) => {
      const start = points.get(edge.source_node_id);
      const end = points.get(edge.target_node_id);
      return start && end ? `<path d="M ${start.x} ${start.y} C ${start.x} ${(start.y + end.y) / 2}, ${end.x} ${(start.y + end.y) / 2}, ${end.x} ${end.y}" />` : "";
    }).join("")}
    ${visibleIds.map((nodeId) => {
      const point = points.get(nodeId);
      const node = nodesById.get(nodeId);
      const current = nodeId === selectedId || nodeId === activeOutputId;
      const navigation = previewNodeNavigation(nodeId, workflow);
      const name = previewNodeName(node);
      const description = previewNodeDescription(node, navigation);
      return `<g class="workflow-tree-preview-node" role="button" tabindex="0" data-preview-node-id="${escapeHtml(nodeId)}" data-preview-node-name="${escapeHtml(name)}" data-preview-node-description="${escapeHtml(description)}" aria-label="${escapeHtml(description)}"><title>${escapeHtml(name)}</title><circle class="${current ? "current" : ""}" cx="${point.x}" cy="${point.y}" r="${current ? 3.6 : 2.5}" /></g>`;
    }).join("")}
  </svg>`;
  canvasPreviewPlane.querySelectorAll("[data-preview-node-id]").forEach((item) => {
    const nodeId = item.dataset.previewNodeId;
    const name = item.dataset.previewNodeName || "";
    item.addEventListener("click", (event) => {
      event.stopPropagation();
      navigateFromPreviewNode(nodeId);
    });
    item.addEventListener("mouseenter", (event) => showCanvasPreviewTooltip(name, event));
    item.addEventListener("mousemove", (event) => moveCanvasPreviewTooltip(event));
    item.addEventListener("mouseleave", hideCanvasPreviewTooltip);
    item.addEventListener("focus", () => showCanvasPreviewTooltip(name));
    item.addEventListener("blur", hideCanvasPreviewTooltip);
    item.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" && event.key !== " ") return;
      event.preventDefault();
      navigateFromPreviewNode(nodeId);
    });
  });
}

function previewNodeNavigation(nodeId, workflow = activeWorkflow()) {
  const stageCopy = workflow?.definition_snapshot?.locales?.[locale]?.stages || {};
  const stageLabel = (stageId, fallback) => localizedReferenceTitle(stageCopy[stageId]?.label || fallback || stageId);
  if (!workflow) {
    const owningScopeId = scopeIdForPreviewNode(nodeId);
    const progressStep = (activeSession()?.progress || []).find((step) => step.scope_id === owningScopeId);
    return {
      scopeId: owningScopeId || defaultLocalScopeId(),
      stageId: progressStep?.workflow_stage_id || "",
      stageLabel: localizedReferenceTitle(progressStep?.label || ""),
    };
  }
  if ((workflow.source_node_ids || []).includes(nodeId) || nodeId === workflow.keyword_node_id) {
    return { scopeId: workflow.foundation_scope_id || "scope-global", stageId: "input", stageLabel: stageLabel("input", t("workflowStrip.brief")) };
  }
  if (nodeId === workflow.operation_node_id) {
    return { scopeId: workflow.comparison_scope_id || workflow.foundation_scope_id || "scope-global", stageId: "four_futures", stageLabel: stageLabel("four_futures", t("workflowStrip.whatIf")) };
  }
  if ((workflow.branch_node_ids || []).includes(nodeId)) {
    return { scopeId: workflow.branch_scope_ids?.[nodeId] || workflow.comparison_scope_id || "scope-global", stageId: "four_futures", stageLabel: stageLabel("four_futures", t("workflowStrip.whatIf")) };
  }
  if (nodeId === workflow.discussion_node_id) {
    const branchId = workflow.selected_branch_node_id || "";
    return { scopeId: workflow.branch_scope_ids?.[branchId] || activeScopeId || "scope-global", stageId: "tools", stageLabel: stageLabel("tools", t("workflowStrip.methods")) };
  }
  if (nodeId === workflow.active_scenario_node_id) {
    const branchId = workflow.selected_branch_node_id || "";
    return { scopeId: workflow.branch_scope_ids?.[branchId] || activeScopeId || "scope-global", stageId: "scenario", stageLabel: stageLabel("scenario", t("workflowStrip.outcomes")) };
  }
  const owningScopeId = scopeIdForPreviewNode(nodeId);
  const progressStep = (activeSession()?.progress || []).find((step) => step.scope_id === owningScopeId);
  if (progressStep) {
    return {
      scopeId: owningScopeId,
      stageId: progressStep.workflow_stage_id || "",
      stageLabel: stageLabel(progressStep.workflow_stage_id || "", progressStep.label || ""),
    };
  }
  return { scopeId: owningScopeId || activeScopeId || defaultLocalScopeId(), stageId: "", stageLabel: "" };
}

function scopeIdForPreviewNode(nodeId) {
  const scopes = activeInteraction?.scopes || [];
  const explicit = scopes.find((scope) => {
    const selector = scope.selector || {};
    return [
      ...(selector.node_ids || []),
      ...(selector.root_node_ids || []),
      ...(scope.snapshot_node_ids || []),
    ].includes(nodeId);
  });
  return explicit?.id || defaultLocalScopeId();
}

function previewNodeName(node) {
  return localizedReferenceTitle(node?.title || nodeTypeLabel(node?.type || "node"));
}

function previewNodeDescription(node, navigation) {
  const title = previewNodeName(node);
  const type = nodeTypeLabel(node?.type || "node");
  const status = statusLabel(node?.status || "draft");
  const target = navigation?.stageLabel ? `${navigation.stageLabel} · ${localizedReferenceTitle((activeInteraction?.scopes || []).find((scope) => scope.id === navigation.scopeId)?.label || navigation.scopeId)}` : localizedReferenceTitle(navigation?.scopeId || "");
  return [title, type, status, target].filter(Boolean).join(" / ");
}

function showCanvasPreviewTooltip(label, event = null) {
  if (!canvasPreviewTooltip || !label) return;
  canvasPreviewTooltip.textContent = label;
  canvasPreviewTooltip.classList.add("visible");
  canvasPreviewTooltip.setAttribute("aria-hidden", "false");
  moveCanvasPreviewTooltip(event);
}

function moveCanvasPreviewTooltip(event = null) {
  if (!canvasPreviewTooltip || !canvasPreviewTooltip.classList.contains("visible")) return;
  if (!event) {
    canvasPreviewTooltip.style.left = "50%";
    canvasPreviewTooltip.style.top = "10px";
    canvasPreviewTooltip.style.transform = "translateX(-50%)";
    return;
  }
  const rect = canvasPreviewTooltip.parentElement?.getBoundingClientRect();
  if (!rect) return;
  const left = Math.min(rect.width - 12, Math.max(12, event.clientX - rect.left + 10));
  const top = Math.min(rect.height - 12, Math.max(12, event.clientY - rect.top + 10));
  canvasPreviewTooltip.style.left = `${left}px`;
  canvasPreviewTooltip.style.top = `${top}px`;
  canvasPreviewTooltip.style.transform = "none";
}

function hideCanvasPreviewTooltip() {
  if (!canvasPreviewTooltip) return;
  canvasPreviewTooltip.classList.remove("visible");
  canvasPreviewTooltip.setAttribute("aria-hidden", "true");
}

function navigateFromPreviewNode(nodeId) {
  const workflow = activeWorkflow();
  const node = findNode(nodeId);
  const navigation = previewNodeNavigation(nodeId, workflow);
  if (workflow?.session_id) activeSessionId = workflow.session_id;
  const nodeName = previewNodeName(node);
  const label = previewNodeDescription(node, navigation);
  const message = locale === "zh"
    ? `是否回到「${nodeName}」对应的进度？\n${label}`
    : `Return to the progress marker for "${nodeName}"?\n${label}`;
  if (!window.confirm(message)) return;
  runUiAction(() => setActiveScope(navigation.scopeId || defaultLocalScopeId(), { stageId: navigation.stageId || "" }));
}

function previewTreeLayers(nodes, edges) {
  const ids = nodes.slice(0, 12).map((node) => node.id);
  const incoming = new Map(ids.map((id) => [id, 0]));
  edges.forEach((edge) => {
    if (incoming.has(edge.target_node_id) && incoming.has(edge.source_node_id)) incoming.set(edge.target_node_id, incoming.get(edge.target_node_id) + 1);
  });
  const roots = ids.filter((id) => !incoming.get(id));
  const rest = ids.filter((id) => incoming.get(id));
  return [roots, rest].filter((layer) => layer.length);
}

function renderCommandProposals() {
  const proposals = activeInteraction?.command_proposals || [];
  commandProposals.innerHTML = proposals.length
    ? proposals.map((proposal) => `
      <article class="command-card">
        <p>${escapeHtml(proposal.title)}</p>
        <small>${escapeHtml(t(`command.${proposal.status}`))} · ${escapeHtml(proposal.action)}</small>
        ${proposal.status === "proposed" ? `
          <div class="command-actions">
            <button type="button" data-command-id="${escapeHtml(proposal.id)}" data-command-resolution="approved">${t("command.approve")}</button>
            <button type="button" data-command-id="${escapeHtml(proposal.id)}" data-command-resolution="rejected">${t("command.reject")}</button>
          </div>
        ` : ""}
      </article>
    `).join("")
    : `<p class="empty-panel">${escapeHtml(t("navigator.none"))}</p>`;
  commandProposals.querySelectorAll("[data-command-id]").forEach((button) => {
    button.addEventListener("click", () => resolveCommand(button.dataset.commandId, button.dataset.commandResolution));
  });
}

async function setActiveScope(scopeId, options = {}) {
  const session = activeSession();
  if (!scopeId || !activeProject || !session) return;
  previewFocusedStageId = options.stageId || "";
  if (scopeId === activeScopeId && session.active_scope_id === scopeId) {
    renderInteraction();
    renderCanvasPreview();
    return;
  }
  try {
    if (session.active_scope_id !== scopeId) {
      await requestJson(`/api/projects/${activeProject.id}/conversations/${session.id}`, {
        method: "PATCH",
        body: JSON.stringify(withExpectedRevision({ active_scope_id: scopeId })),
      });
    }
    // Keep the next canvas refresh on the same canonical Scope while also updating
    // its revision. A navigator selection is therefore a session selection, not a
    // temporary client-side filter.
    activeScopeId = scopeId;
    await loadCanvas();
  } catch (error) {
    setStatus(canvasStatus, "error");
    canvasOutput.textContent = error.message;
  }
}

function openCanvasFocus() {
  if (!canvasFocusLayer) return;
  canvasFocusLayer.classList.add("open");
  canvasFocusLayer.setAttribute("aria-hidden", "false");
  canvas.classList.add("canvas-focus-open");
  requestAnimationFrame(() => {
    // Opening the right-side preview always reveals the original, full editable
    // canvas — not a scope-filtered substitute.
    zoom = fittedScopeZoom(activeCanvas);
    renderCanvas();
  });
}

function closeCanvasFocus() {
  if (!canvasFocusLayer) return;
  canvasFocusLayer.classList.remove("open");
  canvasFocusLayer.setAttribute("aria-hidden", "true");
  canvas.classList.remove("canvas-focus-open");
}

async function submitConversationMessage(event) {
  event.preventDefault();
  const session = activeSession();
  const typedBody = conversationInput.value.trim();
  const selectedOptions = selectedQuickInputs(session);
  if (!activeProject || !session || (!typedBody && !selectedOptions.length)) return;
  const selectedActions = new Set(selectedOptions.map((option) => option.action));
  if (selectedActions.has("run_four_futures")) {
    clearQuickInputs(session);
    await runWorkflowOperation();
    return;
  }
  if (selectedActions.has("confirm_keywords")) {
    clearQuickInputs(session);
    await advanceConversationGuide({ action: "confirm_keywords" });
    return;
  }
  if (selectedActions.has("select_branch")) {
    const workflow = activeWorkflow();
    const selectedBranch = selectedOptions.find((option) => option.action === "select_branch" && option.body);
    clearQuickInputs(session);
    if (workflow?.id && selectedBranch?.body) await selectWorkflowBranch(workflow.id, selectedBranch.body);
    return;
  }
  if (selectedActions.has("tool_select")) {
    const toolIds = selectedOptions.filter((option) => option.action === "tool_select").map((option) => option.body).filter(Boolean);
    clearQuickInputs(session);
    await applySelectedDiscussionTools(toolIds);
    await runSelectedDiscussionNode();
    return;
  }
  if (selectedActions.has("run_scenario")) {
    clearQuickInputs(session);
    await runSelectedDiscussionNode();
    return;
  }
  const selectedBody = selectedOptions.map((option) => option.body || option.label).filter(Boolean).join("\n");
  const body = (typedBody || selectedBody).trim();
  if (!body) return;
  const stage = session.guide?.stage_id || "";
  const isGuidedEntry = stage === "start" || ["frame_focus", "frame_assumptions", "frame_stakeholders", "frame_tensions"].includes(stage);
  const payload = isGuidedEntry
    ? { action: stage === "start" ? "begin" : "answer", body, input_perspective: conversationPerspective }
    : { body, scope_id: activeScopeId, input_perspective: conversationPerspective };
  await requestJson(`/api/projects/${activeProject.id}/conversations/${session.id}/${isGuidedEntry ? "guide-actions" : "messages"}`, {
    method: "POST",
    body: JSON.stringify(withExpectedRevision(payload)),
  });
  conversationInput.value = "";
  clearQuickInputs(session);
  await loadCanvas();
}

function handleQuickInput(action, body = "", label = "") {
  const session = activeSession();
  if (!session) return;
  toggleQuickInputSelection({ action, body, label: label || body || action });
  renderConversationGuide(session);
}

async function advanceConversationGuide(payload) {
  const session = activeSession();
  if (!activeProject || !session) return;
  await requestJson(`/api/projects/${activeProject.id}/conversations/${session.id}/guide-actions`, {
    method: "POST",
    body: JSON.stringify(withExpectedRevision(payload)),
  });
  await loadCanvas({ preserveView: false });
}

async function runWorkflowOperation() {
  const workflow = activeWorkflow();
  if (!activeProject || !workflow?.operation_node_id) return;
  setStatus(canvasStatus, "running");
  try {
    await requestJson(`/api/projects/${activeProject.id}/nodes/${workflow.operation_node_id}/run`, {
      method: "POST",
      body: JSON.stringify(withExpectedRevision({ session_id: activeSessionId })),
      requiresApiKey: true,
    });
    await loadCanvas({ preserveView: false, autoStartBranchImages: true });
  } catch (error) {
    setStatus(canvasStatus, "error");
    canvasOutput.textContent = error.message;
  }
}

function pendingBranchImageNodes() {
  return (activeCanvas?.nodes || []).filter((node) => {
    const payload = node.payload || {};
    const branch = payload.scenario_branch;
    if (!branch || payload.image_url) return false;
    const status = payload.image_status || branch.image_status || "";
    return ["pending", "generating"].includes(status);
  });
}

function replaceNodeInGraph(graph, updatedNode) {
  if (!graph?.nodes || !updatedNode?.id) return;
  graph.nodes = graph.nodes.map((node) => node.id === updatedNode.id ? updatedNode : node);
}

function applyGeneratedBranchImage(updatedNode) {
  if (!updatedNode?.id) return;
  replaceNodeInGraph(activeCanvas, updatedNode);
  replaceNodeInGraph(activeProjection, updatedNode);
  renderInteraction();
  renderCanvas();
}

function markBranchImageFailed(nodeId, message) {
  const node = findNode(nodeId);
  if (!node) return;
  const payload = node.payload || {};
  const branch = payload.scenario_branch || {};
  const updatedNode = {
    ...node,
    payload: {
      ...payload,
      image_status: "failed",
      image_error: message || t("workflow.imageFailed"),
      scenario_branch: {
        ...branch,
        image_status: "failed",
        image_error: message || t("workflow.imageFailed"),
      },
    },
  };
  applyGeneratedBranchImage(updatedNode);
}

async function queuePendingBranchImages() {
  if (branchImageQueueRunning || !activeProject) return;
  if (!tabApiKey && !hasServerModelAccess()) return;
  const firstPending = pendingBranchImageNodes().find((node) => !branchImageInFlight.has(node.id));
  if (!firstPending) return;
  branchImageQueueRunning = true;
  try {
    let nextNode = firstPending;
    while (nextNode) {
      branchImageInFlight.add(nextNode.id);
      try {
        const result = await requestJson(`/api/projects/${activeProject.id}/nodes/${nextNode.id}/generate-image`, {
          method: "POST",
          body: JSON.stringify({ session_id: activeSessionId }),
          requiresApiKey: true,
        });
        applyGeneratedBranchImage(result.node);
      } catch (error) {
        canvasOutput.textContent = error.message;
        markBranchImageFailed(nextNode.id, error.message);
      } finally {
        branchImageInFlight.delete(nextNode.id);
      }
      nextNode = pendingBranchImageNodes().find((node) => !branchImageInFlight.has(node.id));
    }
  } finally {
    branchImageQueueRunning = false;
  }
}

async function applySelectedDiscussionTools(toolIds) {
  const workflow = activeWorkflow();
  const discussion = findNode(workflow?.discussion_node_id);
  const selectedToolIds = new Set(toolIds || []);
  if (!activeProject || !discussion || !selectedToolIds.size) return;
  const tools = (discussion.config?.tools || []).map((tool) =>
    selectedToolIds.has(tool.id) ? { ...tool, selected: true } : tool,
  );
  await requestJson(`/api/projects/${activeProject.id}/nodes/${discussion.id}`, {
    method: "PATCH",
    body: JSON.stringify(withExpectedRevision({ config: { tools }, session_id: activeSessionId })),
  });
  await loadCanvas({ preserveView: false });
}

async function runSelectedDiscussionNode() {
  const workflow = activeWorkflow();
  const discussion = findNode(workflow?.discussion_node_id);
  if (!activeProject || !discussion) return;
  setStatus(canvasStatus, "running");
  await requestJson(`/api/projects/${activeProject.id}/nodes/${discussion.id}/run`, {
    method: "POST",
    body: JSON.stringify(withExpectedRevision({ session_id: activeSessionId })),
    requiresApiKey: true,
  });
  await loadCanvas({ preserveView: false });
}

async function resolveCommand(commandId, resolution) {
  if (!activeProject || !commandId || !resolution) return;
  await requestJson(`/api/projects/${activeProject.id}/command-proposals/${commandId}/resolve`, {
    method: "POST",
    body: JSON.stringify(withExpectedRevision({ resolution })),
  });
  await loadCanvas();
}

function renderPlane() {
  const size = canvasBaseSize();
  canvasContent.style.width = `${size.width * zoom}px`;
  canvasContent.style.height = `${size.height * zoom}px`;
  canvasPlane.style.width = `${size.width}px`;
  canvasPlane.style.height = `${size.height}px`;
  canvasPlane.style.transform = `scale(${zoom})`;
  updateZoomControls();
  renderEdges(size);
}

function renderEdges(size = canvasBaseSize()) {
  const graph = displayGraph();
  if (!graph) return;
  edgesLayer.innerHTML = "";
  edgesLayer.setAttribute("width", String(size.width));
  edgesLayer.setAttribute("height", String(size.height));
  edgesLayer.removeAttribute("viewBox");

  for (const edge of graph.edges || []) {
    const sourceEl = nodesLayer.querySelector(`[data-node-id="${cssEscape(edge.source_node_id)}"]`);
    const targetEl = nodesLayer.querySelector(`[data-node-id="${cssEscape(edge.target_node_id)}"]`);
    if (!sourceEl || !targetEl) continue;
    edgesLayer.append(renderEdge(sourceEl, targetEl, edge));
  }
  if (connectionDraft) {
    edgesLayer.append(renderConnectionPreview());
  }
}

function canvasBaseSize() {
  const nodes = displayGraph()?.nodes || [];
  const contentBounds = nodes.reduce(
    (bounds, node) => {
      const element = nodesLayer.querySelector(`[data-node-id="${cssEscape(node.id)}"]`);
      const width = element?.offsetWidth || node.size?.width || 240;
      const height = element?.offsetHeight || node.size?.height || 170;
      return {
        width: Math.max(bounds.width, node.position.x + width + 120),
        height: Math.max(bounds.height, node.position.y + height + 120),
      };
    },
    { width: 0, height: 0 },
  );
  return {
    width: Math.max(workspace.clientWidth, contentBounds.width, 1180),
    height: Math.max(workspace.clientHeight, contentBounds.height, 620),
  };
}

function renderEdge(sourceEl, targetEl, edge) {
  const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  const d = edgePath(portPoint(sourceEl, "out"), portPoint(targetEl, "in"));
  path.setAttribute("d", d);
  path.dataset.kind = edge.edge_kind;
  const hit = document.createElementNS("http://www.w3.org/2000/svg", "path");
  hit.setAttribute("d", d);
  hit.classList.add("edge-hit");
  hit.dataset.edgeId = edge.id;
  if (!edge.presentation_only) {
    hit.addEventListener("contextmenu", (event) => openEdgeMenu(event, edge));
    group.addEventListener("contextmenu", (event) => openEdgeMenu(event, edge));
  } else {
    hit.style.pointerEvents = "none";
  }
  group.append(path, hit);
  return group;
}

function renderConnectionPreview() {
  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.setAttribute("d", edgePath(connectionDraft.start, connectionDraft.current));
  path.dataset.kind = "preview";
  path.classList.add("edge-preview");
  return path;
}

function edgePath(start, end) {
  const mid = Math.max(36, Math.abs(end.x - start.x) * 0.45);
  return `M ${start.x} ${start.y} C ${start.x + mid} ${start.y}, ${end.x - mid} ${end.y}, ${end.x} ${end.y}`;
}

function portPoint(element, role) {
  const port = element.querySelector(`[data-port-role="${role}"]`);
  const planeRect = canvasPlane.getBoundingClientRect();
  if (port) {
    const portRect = port.getBoundingClientRect();
    return {
      x: (portRect.left + portRect.width / 2 - planeRect.left) / zoom,
      y: (portRect.top + portRect.height / 2 - planeRect.top) / zoom,
    };
  }
  const rect = element.getBoundingClientRect();
  const x = role === "out" ? element.offsetLeft + element.offsetWidth : element.offsetLeft;
  return {
    x,
    y: (rect.top + rect.height / 2 - planeRect.top) / zoom,
  };
}

function nodeBox(element) {
  return {
    x: element.offsetLeft,
    y: element.offsetTop,
    width: element.offsetWidth,
    height: element.offsetHeight,
  };
}

function renderNode(node) {
  const article = document.createElement("article");
  article.className = `node ${node.type}-node ${node.status || ""}`;
  article.dataset.nodeId = node.id;
  article.style.left = `${node.position.x}px`;
  article.style.top = `${node.position.y}px`;
  if (node.size?.width) article.style.width = `${node.size.width}px`;

  article.innerHTML = `
    <button class="port port-in" type="button" data-port-role="in" aria-label="${t("node.inputPort")}"></button>
    <button class="port port-out" type="button" data-port-role="out" aria-label="${t("node.outputPort")}"></button>
    <header>
      <span>${escapeHtml(nodeTypeLabel(node.type))}</span>
      <span>${escapeHtml(statusLabel(node.status))}</span>
    </header>
    ${renderNodeBody(node)}
    <footer>
      <span>${escapeHtml(localizedReferenceTitle(node.title))}</span>
      <span>${escapeHtml(node.active_run_id || t("node.revision", { count: 1 }))}</span>
    </footer>
  `;

  article.addEventListener("pointerdown", (event) => beginDrag(event, node));
  article.addEventListener("contextmenu", (event) => openNodeMenu(event, node));
  article.addEventListener("dblclick", (event) => {
    if (event.target.closest("button, textarea, input, select, label")) return;
    if (node.payload?.text) openTextReader(node);
  });
  article.querySelector('[data-port-role="out"]').addEventListener("pointerdown", (event) => {
    beginConnection(event, node, article);
  });
  article.querySelector('[data-port-role="in"]').addEventListener("pointerdown", (event) => {
    event.stopPropagation();
  });
  article.querySelectorAll("[data-tool-id]").forEach((button) => {
    button.addEventListener("click", (event) => toggleTool(event, node));
  });
  article.querySelectorAll("[data-output-type]").forEach((button) => {
    button.addEventListener("click", (event) => setOutputType(event, node));
  });
  const runButton = article.querySelector("[data-run-modify], [data-run-operation]");
  if (runButton) {
    runButton.addEventListener("click", (event) => runNode(event, node));
  }
  article.querySelectorAll("[data-select-workflow-branch]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      runUiAction(() => selectWorkflowBranch(button.dataset.selectWorkflowBranch, node.id));
    });
  });
  article.querySelectorAll("[data-open-image]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      openImageViewer(node);
    });
  });
  article.querySelectorAll("[data-upload-node-file]").forEach((input) => {
    input.addEventListener("change", (event) => uploadNodeFile(event, node));
    input.addEventListener("pointerdown", (event) => event.stopPropagation());
  });
  article.querySelectorAll("[data-upload-image-file]").forEach((input) => {
    input.addEventListener("change", (event) => uploadImageNodeFile(event, node));
    input.addEventListener("pointerdown", (event) => event.stopPropagation());
  });
  article.querySelectorAll("[data-open-full-text]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      openTextReader(node);
    });
  });
  const textarea = article.querySelector("textarea");
  if (textarea) {
    textarea.addEventListener("blur", () => updateNodePayload(node, { text: textarea.value }));
    textarea.addEventListener("pointerdown", (event) => event.stopPropagation());
  }
  return article;
}

function renderNodeBody(node) {
  if (node.type === "modify") {
    const tools = (node.config?.tools || []).filter((tool) => tool.enabled !== false);
    const outputType = node.config?.output_type || "text";
    const recommendation = outputRecommendation(node);
    const outputRows = ["text", "image", "multimodal"]
      .map(
        (type) => `
          <button class="output-row ${outputType === type ? "selected" : ""}" type="button" data-output-type="${type}">
            <span class="dot"></span><span>${outputLabel(type)}</span>
          </button>
        `,
      )
      .join("");
    return `
      <div class="modify-summary">${escapeHtml(t("modify.toolsInSidebar", { count: tools.filter((tool) => tool.selected).length }))}</div>
      <div class="output-stack">
        <div class="micro-label">${t("common.output")}</div>
        ${outputRows}
        ${renderRecommendation(recommendation)}
      </div>
      <div class="node-actions">
        <span>${escapeHtml(t(`composition.${node.config?.composition || "parallel"}`))}</span>
        <button type="button" data-run-modify>${t("common.run")}</button>
      </div>
    `;
  }

  if (node.type === "operation") {
    const definition = node.config?.definition || {};
    const selectedTools = node.config?.tool_selections || [];
    const runLabel = localizedOperationUiCopy(definition, "run_label") || t("common.run");
    const canRun = Boolean(definition.execution?.executor);
    return `
      <div class="operation-definition">
        <strong>${escapeHtml(localizedOperationCopy(definition, "label") || localizedReferenceTitle(node.title))}</strong>
        <span>${escapeHtml(localizedOperationCopy(definition, "description") || t("nodes.operationDefault"))}</span>
      </div>
      <div class="node-actions">
        <span>${escapeHtml(selectedTools.length ? t("operation.toolsSelected", { count: selectedTools.length }) : t("operation.definition"))}</span>
        ${canRun
          ? `<button type="button" data-run-operation>${escapeHtml(runLabel)}</button>`
          : `<span>${escapeHtml(outputLabel(node.config?.output_profile || "text"))}</span>`}
      </div>
    `;
  }

  if (node.payload?.scenario_branch) {
    return renderScenarioBranchBody(node);
  }

  if (node.type === "image") {
    return `
      ${node.produced_by_run_id ? "" : renderImageUploadControl(node)}
      ${renderImageFrame(node)}
      ${renderResultPreview(node, "image")}
      ${node.payload?.image_error ? `<p class="image-error">${escapeHtml(node.payload.image_error)}</p>` : ""}
    `;
  }

  if (node.type === "multimodal") {
    return `
      ${renderImageFrame(node)}
      ${renderResultPreview(node, "text+image")}
      ${node.payload?.image_error ? `<p class="image-error">${escapeHtml(node.payload.image_error)}</p>` : ""}
    `;
  }

  if (node.type === "upload") {
    return renderUploadNodeBody(node);
  }

  if (node.type === "text" || node.type === "conversation") {
    if (node.produced_by_run_id || ["success", "failed", "stale"].includes(node.status)) {
      return renderGeneratedTextBody(node);
    }
    return renderEditableTextBody(node);
  }

  return `<p>${escapeHtml(node.payload?.text || "")}</p>`;
}

function renderScenarioBranchBody(node) {
  const branch = node.payload?.scenario_branch || {};
  const workflow = workflowForBranch(node.id);
  const isSelected = workflow?.selected_branch_node_id === node.id;
  const canChoose = workflow?.status === "awaiting_selection";
  return `
    <div class="scenario-branch">
      <strong>${escapeHtml(localizedReferenceTitle(branch.strategy_label || node.title))}</strong>
      <p>${escapeHtml(branch.what_if || previewText(node.payload?.text || ""))}</p>
      ${branch.future_premise ? `<span>${escapeHtml(branch.future_premise)}</span>` : ""}
    </div>
    <div class="node-actions">
      <span>${escapeHtml(isSelected ? t("workflow.chosen") : (canChoose ? t("workflow.awaitingSelection") : "scenario"))}</span>
      ${canChoose ? `<button type="button" data-select-workflow-branch="${escapeHtml(workflow.id)}">${escapeHtml(t("workflow.choose"))}</button>` : ""}
    </div>
  `;
}

function renderImageUploadControl(node) {
  const filename = node.payload?.filename || t("node.noImageUploaded");
  return `
    <label class="node-file-control">
      <span>${t("common.chooseImage")}</span>
      <input type="file" accept="image/jpeg,image/png,image/webp,image/gif" data-upload-image-file />
    </label>
    <p class="upload-filename">${escapeHtml(filename)}</p>
  `;
}

function renderEditableTextBody(node) {
  const hasText = Boolean(String(node.payload?.text || "").trim());
  return `
    <textarea aria-label="${escapeHtml(localizedReferenceTitle(node.title))}">${escapeHtml(node.payload?.text || "")}</textarea>
    <div class="node-actions input-node-actions">
      <span>${t("common.inputText")}</span>
      <button type="button" data-open-full-text ${hasText ? "" : "disabled"}>${t("common.openFullText")}</button>
    </div>
  `;
}

function renderGeneratedTextBody(node) {
  return renderResultPreview(node, node.payload?.requested_output_type || "text");
}

function renderUploadNodeBody(node) {
  const hasText = Boolean(String(node.payload?.text || "").trim());
  const filename = node.payload?.filename || t("node.noFileUploaded");
  return `
    <label class="node-file-control">
      <span>${t("common.chooseFile")}</span>
      <input type="file" accept=".pdf,.docx,.txt,.md" data-upload-node-file />
    </label>
    <p class="upload-filename">${escapeHtml(filename)}</p>
    <p class="generated-preview">${escapeHtml(previewText(node.payload?.text || t("node.uploadPrompt")))}</p>
    <div class="node-actions input-node-actions">
      <span>${escapeHtml(node.payload?.document_type || t("common.document"))}</span>
      <button type="button" data-open-full-text ${hasText ? "" : "disabled"}>${t("common.openFullText")}</button>
    </div>
  `;
}

function renderResultPreview(node, label) {
  const fallback = node.type === "image" ? t("node.imageFallback") : t("node.multimodalFallback");
  const displayText = previewTextForNode(node) || fallback;
  return `
    <p class="generated-preview">${escapeHtml(previewText(displayText))}</p>
    <div class="node-actions">
      <span>${escapeHtml(label)}</span>
      <button type="button" data-open-full-text>${t("common.openFullText")}</button>
    </div>
  `;
}

function renderImageFrame(node) {
  if (node.payload?.image_url) {
    return `
      <figure class="generated-image-frame">
        <button type="button" data-open-image aria-label="${t("node.openImage")}">
        <img src="${escapeHtml(node.payload.image_url)}" alt="${escapeHtml(node.payload?.semantic_summary || node.title || t("common.generatedImage"))}" />
        </button>
      </figure>
    `;
  }
  return `<div class="image-placeholder">${t("common.semanticImage")}</div>`;
}

function previewText(value) {
  const text = stripPreviewLabels(
    stripTextArtifacts(String(value || ""))
      .replace(/\r\n/g, "\n")
      .replace(/\\n/g, "\n")
      .replace(/[ \t]+/g, " ")
      .replace(/\n{3,}/g, "\n\n")
      .trim(),
  );
  if (!text) return "";
  const paragraphs = text.split(/\n\s*\n/).map(stripPreviewLabels).filter(Boolean);
  const firstParagraph = paragraphs[0] || text;
  const clipped = firstParagraph.length > 120 ? firstParagraph.slice(0, 120).trimEnd() : firstParagraph;
  const hasMore = text.length > firstParagraph.length || firstParagraph.length > clipped.length;
  return hasMore ? `${clipped}...` : clipped;
}

function previewTextForNode(node) {
  const text = plainTextFromValue(node.payload?.text || "");
  if (text) return text;
  return primaryModelText(node.payload?.model_output);
}

function stripPreviewLabels(text) {
  return String(text || "")
    .replace(/^(摘要|生成内容|summary|generated text)\s*[:：]?\s*/i, "")
    .replace(/^[a-z][a-z0-9_ ]{2,40}\s*[:：]\s*/i, "")
    .trim();
}

function outputRecommendation(node) {
  if (node.config?.output_recommendation) {
    return normalizeRecommendation(node.config.output_recommendation);
  }
  return {
    type: "text",
    readiness: "medium",
    reason: "early transformations are easier to review as text",
    warnings: [],
    items: [],
  };
}

function normalizeRecommendation(recommendation) {
  const type = ["text", "image", "multimodal"].includes(recommendation?.type) ? recommendation.type : "text";
  const items = Array.isArray(recommendation?.items)
    ? recommendation.items
        .filter((item) => item && typeof item === "object")
        .map((item) => ({
          tool_id: String(item.tool_id || ""),
          label: String(item.label || item.tool_id || ""),
          type: ["text", "image", "multimodal"].includes(item.type) ? item.type : "text",
          readiness: String(item.readiness || "medium"),
          reason: String(item.reason || ""),
          warnings: Array.isArray(item.warnings) ? item.warnings.map(String).filter(Boolean) : [],
        }))
    : [];
  return {
    type,
    readiness: String(recommendation?.readiness || "medium"),
    reason: String(recommendation?.reason || ""),
    warnings: Array.isArray(recommendation?.warnings) ? recommendation.warnings.map(String).filter(Boolean) : [],
    items,
  };
}

function renderRecommendation(recommendation) {
  const items = recommendation.items || [];
  if (!items.length) return "";
  const itemRows = items
    .map(
      (item) => `
        <li class="recommendation-item" tabindex="0">
          <span class="recommendation-tool">${escapeHtml(localizedToolCopy(toolById(item.tool_id) || item, "label"))}</span>
          <strong>${escapeHtml(outputLabel(item.type))}</strong>
          ${item.reason ? `<span class="tool-tooltip recommendation-tooltip" role="tooltip">${escapeHtml(item.reason)}</span>` : ""}
        </li>
      `,
    )
    .join("");
  return `
    <div class="recommendation">
      <ul class="recommendation-items">${itemRows}</ul>
    </div>
  `;
}

function outputLabel(type) {
  return {
    text: t("output.text"),
    image: t("output.image"),
    multimodal: t("output.multimodal"),
  }[type] || type;
}

function summarizeCanvas(graph) {
  return {
    id: graph.id,
    project_id: graph.project_id,
    nodes: graph.nodes.length,
    edges: graph.edges.length,
    runs: graph.runs.length,
    updated_at: graph.updated_at,
  };
}

function findNode(id) {
  return activeCanvas?.nodes.find((node) => node.id === id);
}

async function renameProject(project = activeProject) {
  if (!project) return;
  const title = window.prompt(t("project.renamePrompt"), project.title || t("project.untitled"));
  if (title === null) return;
  const trimmed = title.trim();
  if (!trimmed) return;
  const { project: updated } = await requestJson(`/api/projects/${project.id}`, {
    method: "PATCH",
    body: JSON.stringify({ title: trimmed }),
  });
  if (activeProject?.id === updated.id) {
    activeProject = { ...activeProject, ...updated };
    updateCanvasTitle(updated.title);
  }
  await loadProjects();
}

async function addNode(type, options = {}) {
  if (!activeProject || !activeCanvas) return;
  const offset = activeCanvas.nodes.length * 24;
  const payload = {
    type,
    title: options.title || titleForType(type),
    position: { x: 92 + offset, y: 110 + offset },
    payload: { text: defaultTextForType(type) },
    session_id: activeSessionId,
    ...options,
  };
  await requestJson(`/api/projects/${activeProject.id}/nodes`, {
    method: "POST",
    body: JSON.stringify(withExpectedRevision(payload)),
  });
  await loadCanvas();
}

function openFoundationWorkflowDialog() {
  conversationInput?.focus();
}

async function selectWorkflowBranch(workflowId, branchNodeId) {
  if (!activeProject || !workflowId || !branchNodeId) return;
  const result = await requestJson(`/api/projects/${activeProject.id}/workflows/${workflowId}/select-branch`, {
    method: "POST",
    body: JSON.stringify(withExpectedRevision({ branch_node_id: branchNodeId, session_id: activeSessionId })),
  });
  if (result.session?.id) activeSessionId = result.session.id;
  activeScopeId = result.scope_id || activeScopeId;
  previewFocusedStageId = "tools";
  await loadCanvas({ preserveView: true });
}

async function toggleTool(event, node) {
  event.stopPropagation();
  const toolId = event.currentTarget.dataset.toolId;
  const tool = (node.config?.tools || []).find((item) => item.id === toolId);
  await setToolSelection(node, toolId, !tool?.selected);
}

async function setToolSelection(node, toolId, selected) {
  if (!activeProject || !node || !toolId) return;
  const tools = (node.config?.tools || []).map((tool) =>
    tool.id === toolId ? { ...tool, selected } : tool,
  );
  await requestJson(`/api/projects/${activeProject.id}/nodes/${node.id}`, {
    method: "PATCH",
    body: JSON.stringify(withExpectedRevision({ config: { tools }, session_id: activeSessionId })),
  });
  await loadCanvas();
}

async function setOutputType(event, node) {
  event.stopPropagation();
  const outputType = event.currentTarget.dataset.outputType;
  await requestJson(`/api/projects/${activeProject.id}/nodes/${node.id}`, {
    method: "PATCH",
    body: JSON.stringify(withExpectedRevision({ config: { output_type: outputType }, session_id: activeSessionId })),
  });
  await loadCanvas();
}

function openNodeMenu(event, node) {
  if (event.target.closest("textarea, input")) return;
  event.preventDefault();
  event.stopPropagation();
  contextNodeId = node.id;
  contextEdgeId = null;
  const canOpen = Boolean(node.payload?.text);
  menuOpenFull.disabled = !canOpen;
  menuDelete.textContent = t("menu.deleteNode");
  nodeMenu.classList.remove("hidden");
  const menuRect = nodeMenu.getBoundingClientRect();
  const x = Math.min(event.clientX, window.innerWidth - menuRect.width - 8);
  const y = Math.min(event.clientY, window.innerHeight - menuRect.height - 8);
  nodeMenu.style.left = `${Math.max(8, x)}px`;
  nodeMenu.style.top = `${Math.max(8, y)}px`;
}

function openEdgeMenu(event, edge) {
  event.preventDefault();
  event.stopPropagation();
  contextNodeId = null;
  contextEdgeId = edge.id;
  menuOpenFull.disabled = true;
  menuDelete.textContent = t("menu.deleteEdge");
  nodeMenu.classList.remove("hidden");
  const menuRect = nodeMenu.getBoundingClientRect();
  const x = Math.min(event.clientX, window.innerWidth - menuRect.width - 8);
  const y = Math.min(event.clientY, window.innerHeight - menuRect.height - 8);
  nodeMenu.style.left = `${Math.max(8, x)}px`;
  nodeMenu.style.top = `${Math.max(8, y)}px`;
}

function closeNodeMenu() {
  nodeMenu.classList.add("hidden");
  menuDelete.textContent = t("common.delete");
  contextNodeId = null;
  contextEdgeId = null;
}

async function deleteContextNode() {
  if (!activeProject || (!contextNodeId && !contextEdgeId)) return;
  if (contextEdgeId) {
    const edgeId = contextEdgeId;
    closeNodeMenu();
    setStatus(canvasStatus, "deleting");
    await requestJson(`/api/projects/${activeProject.id}/edges/${edgeId}`, {
      method: "DELETE",
      body: JSON.stringify(withExpectedRevision({ session_id: activeSessionId })),
    });
    await loadCanvas();
    return;
  }
  const node = findNode(contextNodeId);
  const confirmed = window.confirm(t("node.deleteConfirm", { title: node?.title || contextNodeId }));
  if (!confirmed) {
    closeNodeMenu();
    return;
  }
  const nodeId = contextNodeId;
  closeNodeMenu();
  setStatus(canvasStatus, "deleting");
  await requestJson(`/api/projects/${activeProject.id}/nodes/${nodeId}`, {
    method: "DELETE",
    body: JSON.stringify(withExpectedRevision({ session_id: activeSessionId })),
  });
  await loadCanvas();
}

function openContextNodeText() {
  const node = findNode(contextNodeId);
  closeNodeMenu();
  if (node) openTextReader(node);
}

function openTextReader(node) {
  textReaderTitle.textContent = localizedReferenceTitle(node.title || node.type || t("reader.nodeText"));
  renderTextReaderBody(node);
  textReader.classList.remove("hidden");
}

function closeTextReader() {
  textReader.classList.add("hidden");
}

function renderTextReaderBody(node) {
  textReaderBody.replaceChildren();
  const blocks = textBlocksForNode(node);
  if (!blocks.length) {
    textReaderBody.textContent = formatNodeText(node);
    return;
  }
  blocks.forEach((block) => textReaderBody.append(renderTextBlock(block)));
}

function textBlocksForNode(node) {
  const blocks = node.payload?.model_output?.text_blocks;
  if (!Array.isArray(blocks)) return [];
  return blocks.map(normalizeTextBlock).filter(Boolean);
}

function normalizeTextBlock(block) {
  if (!block || typeof block !== "object" || Array.isArray(block)) return null;
  const type = String(block.type || "").trim();
  const title = readableBlockText(block.title).slice(0, 120);
  if (!["callout", "paragraph", "table", "bar_chart", "list", "questions"].includes(type)) return null;
  if (["callout", "paragraph"].includes(type)) {
    const text = readableBlockText(block.text);
    return text ? { type, title, text } : null;
  }
  if (type === "table") {
    const columns = Array.isArray(block.columns) ? block.columns.map(readableBlockText).filter(Boolean).slice(0, 6) : [];
    const rows = Array.isArray(block.rows)
      ? block.rows
        .filter((row) => Array.isArray(row))
        .map((row) => row.map(readableBlockText).slice(0, columns.length || 6))
        .filter((row) => row.some(Boolean))
        .slice(0, 12)
      : [];
    return columns.length && rows.length ? { type, title, columns, rows } : null;
  }
  if (type === "bar_chart") {
    const items = Array.isArray(block.items)
      ? block.items
        .map((item) => ({
          label: readableBlockText(item?.label || item),
          value: Math.max(0, Math.min(5, Number(item?.value) || 0)),
          note: readableBlockText(item?.note),
        }))
        .filter((item) => item.label)
        .slice(0, 8)
      : [];
    return items.length ? { type, title, items } : null;
  }
  const items = Array.isArray(block.items) ? block.items.map(readableBlockText).filter(Boolean).slice(0, 12) : [];
  return items.length ? { type, title, items } : null;
}

function readableBlockText(value) {
  return String(value ?? "")
    .replace(/\r\n/g, "\n")
    .replace(/\\n/g, "\n")
    .replace(/[ \t]+/g, " ")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function renderTextBlock(block) {
  const section = document.createElement("section");
  section.className = `text-block text-block-${block.type}`;
  if (block.title) {
    const heading = document.createElement("h3");
    heading.textContent = block.title;
    section.append(heading);
  }
  if (["callout", "paragraph"].includes(block.type)) {
    const paragraph = document.createElement("p");
    paragraph.textContent = block.text;
    section.append(paragraph);
    return section;
  }
  if (block.type === "table") {
    const scroll = document.createElement("div");
    scroll.className = "text-table-scroll";
    const table = document.createElement("table");
    const head = document.createElement("thead");
    const headRow = document.createElement("tr");
    block.columns.forEach((column) => {
      const cell = document.createElement("th");
      cell.scope = "col";
      cell.textContent = column;
      headRow.append(cell);
    });
    head.append(headRow);
    table.append(head);
    const body = document.createElement("tbody");
    block.rows.forEach((row) => {
      const rowEl = document.createElement("tr");
      block.columns.forEach((_, index) => {
        const cell = document.createElement("td");
        cell.textContent = row[index] || "";
        rowEl.append(cell);
      });
      body.append(rowEl);
    });
    table.append(body);
    scroll.append(table);
    section.append(scroll);
    return section;
  }
  if (block.type === "bar_chart") {
    const chart = document.createElement("div");
    chart.className = "text-bar-chart";
    block.items.forEach((item) => {
      const row = document.createElement("div");
      row.className = "text-bar-row";
      const label = document.createElement("span");
      label.className = "text-bar-label";
      label.textContent = item.label;
      const track = document.createElement("span");
      track.className = "text-bar-track";
      const fill = document.createElement("span");
      fill.className = "text-bar-fill";
      fill.style.width = `${item.value * 20}%`;
      track.append(fill);
      const value = document.createElement("span");
      value.className = "text-bar-value";
      value.textContent = `${item.value}/5`;
      row.append(label, track, value);
      if (item.note) {
        const note = document.createElement("small");
        note.textContent = item.note;
        row.append(note);
      }
      chart.append(row);
    });
    section.append(chart);
    return section;
  }
  const list = document.createElement("ol");
  list.className = block.type === "questions" ? "text-question-list" : "text-list";
  block.items.forEach((item) => {
    const entry = document.createElement("li");
    entry.textContent = item;
    list.append(entry);
  });
  section.append(list);
  return section;
}

function openImageViewer(node) {
  const imageUrl = node.payload?.image_url;
  if (!imageUrl) return;
  imageViewerTitle.textContent = localizedReferenceTitle(node.title || t("reader.imagePreview"));
  imageViewerImg.src = imageUrl;
  imageViewerCaption.textContent = imageCaptionForNode(node);
  imageViewerImg.alt = imageViewerCaption.textContent || node.title || t("common.generatedImage");
  imageViewer.classList.remove("hidden");
}

function closeImageViewer() {
  imageViewer.classList.add("hidden");
  imageViewerImg.src = "";
  imageViewerImg.alt = "";
  imageViewerCaption.textContent = "";
}

function imageCaptionForNode(node) {
  const semanticSummary = plainTextFromValue(node.payload?.semantic_summary || "");
  if (semanticSummary) return semanticSummary;
  const modelOutput = node.payload?.model_output;
  if (modelOutput && typeof modelOutput === "object") {
    const renderedSummary = plainTextFromValue(modelOutput.semantic_summary || modelOutput.summary || "");
    if (renderedSummary) return renderedSummary;
    const renderedPrimary = previewText(primaryModelText(modelOutput));
    if (renderedPrimary) return renderedPrimary;
  }
  const imagePrompt = plainTextFromValue(node.payload?.image_prompt || "");
  if (imagePrompt) return imagePrompt;
  return previewText(plainTextForNode(node));
}

async function uploadNodeFile(event, node) {
  const file = event.target.files[0];
  if (!file || !activeProject) return;
  event.target.disabled = true;
  setStatus(canvasStatus, "reading");
  const formData = new FormData();
  formData.append("file", file);
  try {
    const result = await requestJson("/api/documents/inspect", {
      method: "POST",
      body: formData,
    });
    const documentPayload = result.document || {};
    await updateNodePayload(node, {
      filename: documentPayload.filename || file.name,
      document_type: documentPayload.type || t("common.document"),
      text: textFromDocumentInspection(documentPayload),
      document: documentPayload,
    });
    setStatus(canvasStatus, "ready");
  } catch (error) {
    setStatus(canvasStatus, "error");
    canvasOutput.textContent = error.message;
  } finally {
    event.target.disabled = false;
  }
}

async function uploadImageNodeFile(event, node) {
  const file = event.target.files[0];
  if (!file || !activeProject) return;
  event.target.disabled = true;
  setStatus(canvasStatus, "reading");
  const formData = new FormData();
  formData.append("file", file);
  try {
    const result = await requestJson("/api/images/upload", {
      method: "POST",
      body: formData,
    });
    const image = result.image || {};
    await updateNodePayload(node, {
      filename: image.filename || file.name,
      mime_type: image.mime_type || file.type,
      image_file: image.image_file || "",
      image_url: image.image_url || "",
      image_source: "upload",
      semantic_status: "available for visual reasoning",
      text: `${t("node.imageReference")}: ${image.filename || file.name}`,
    });
    setStatus(canvasStatus, "ready");
  } catch (error) {
    setStatus(canvasStatus, "error");
    canvasOutput.textContent = error.message;
  } finally {
    event.target.disabled = false;
  }
}

function textFromDocumentInspection(documentPayload) {
  const lines = [
    `Filename: ${documentPayload.filename || "uploaded file"}`,
    `Type: ${documentPayload.type || "document"}`,
  ];
  if (documentPayload.preview) lines.push("", documentPayload.preview);
  if (Array.isArray(documentPayload.paragraphs) && documentPayload.paragraphs.length) {
    lines.push("", "Paragraphs", ...documentPayload.paragraphs.slice(0, 24));
  }
  if (Array.isArray(documentPayload.tables) && documentPayload.tables.length) {
    lines.push("", "Tables", JSON.stringify(documentPayload.tables.slice(0, 4), null, 2));
  }
  if (documentPayload.metadata) {
    lines.push("", "Metadata", JSON.stringify(documentPayload.metadata, null, 2));
  }
  return lines.join("\n").trim() || JSON.stringify(documentPayload, null, 2);
}

function formatNodeText(node) {
  const text = plainTextForNode(node);
  const imagePrompt = node.payload?.image_prompt ? `\n\n${t("reader.imagePrompt")}\n${plainTextFromValue(node.payload.image_prompt)}` : "";
  const semanticSummary = node.payload?.semantic_summary ? `\n\n${t("reader.semanticSummary")}\n${plainTextFromValue(node.payload.semantic_summary)}` : "";
  const imageUrl = node.payload?.image_url ? `\n\n${t("reader.imageUrl")}\n${node.payload.image_url}` : "";
  const imageError = node.payload?.image_error ? `\n\n${t("reader.imageError")}\n${plainTextFromValue(node.payload.image_error)}` : "";
  return `${text}${imagePrompt}${semanticSummary}${imageUrl}${imageError}`.trim() || t("reader.noText");
}

function plainTextForNode(node) {
  const modelOutput = node.payload?.model_output;
  const primary = primaryModelText(modelOutput);
  if (primary) {
    return primary;
  }
  if (modelOutput && typeof modelOutput === "object" && !modelOutput.raw_text) {
    return plainTextFromModelObject(modelOutput);
  }
  return plainTextFromValue(node.payload?.text || "");
}

function primaryModelText(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return "";
  const preferredKeys = [
    "generated_text",
    "written_scenario",
    "scenario",
    "cautionary_scenario",
    "counterfactual_premise",
    "artifact_description",
    "semantic_summary",
    "raw_text",
  ];
  for (const key of preferredKeys) {
    if (Object.prototype.hasOwnProperty.call(value, key)) {
      const rendered = plainTextFromValue(value[key]);
      if (rendered) return rendered;
    }
  }
  return "";
}

function plainTextFromValue(value) {
  if (value == null) return "";
  if (typeof value !== "string") return plainTextFromModelObject(value);
  const trimmed = value.trim();
  const parsed = parseLooseJson(trimmed);
  if (parsed) return plainTextFromModelObject(parsed);
  return stripTextArtifacts(trimmed);
}

function parseLooseJson(text) {
  if (!text || !text.startsWith("{")) return null;
  try {
    return JSON.parse(text);
  } catch {
    const start = text.indexOf("{");
    const end = text.lastIndexOf("}");
    if (start >= 0 && end > start) {
      try {
        return JSON.parse(text.slice(start, end + 1));
      } catch {
        return parseJsonishObject(text.slice(start, end + 1));
      }
    }
    return start >= 0 ? parseJsonishObject(text.slice(start)) : null;
  }
}

function parseJsonishObject(text) {
  const matches = [...text.matchAll(/^\s*"([A-Za-z0-9_]+)"\s*:\s*/gm)];
  if (!matches.length) return null;
  const parsed = {};
  matches.forEach((match, index) => {
    const key = match[1];
    const start = match.index + match[0].length;
    const end = index + 1 < matches.length ? matches[index + 1].index : text.length;
    let value = text.slice(start, end).trim();
    value = value.replace(/,\s*$/, "").replace(/\}\s*$/, "").trim();
    if (value.startsWith('"')) value = value.slice(1);
    if (value.endsWith('"')) value = value.slice(0, -1);
    value = value.replace(/\\n/g, "\n").replace(/\\"/g, '"').trim();
    if (value) parsed[key] = value;
  });
  return Object.keys(parsed).length ? parsed : null;
}

function plainTextFromModelObject(value) {
  if (value == null) return "";
  if (typeof value === "string") return stripTextArtifacts(value);
  if (Array.isArray(value)) {
    return value.map((item) => plainTextFromModelObject(item)).filter(Boolean).join("\n");
  }
  if (typeof value !== "object") return String(value);

  const preferredKeys = [
    "summary",
    "generated_text",
    "scenario",
    "written_scenario",
    "visual_brief",
    "semantic_summary",
    "discussion_questions",
    "source_trace",
    "raw_text",
  ];
  const keys = [
    ...preferredKeys.filter((key) => Object.prototype.hasOwnProperty.call(value, key)),
    ...Object.keys(value).filter((key) => !preferredKeys.includes(key) && key !== "image_prompt" && key !== "text_blocks"),
  ];
  return keys
    .map((key) => {
      const rendered = plainTextFromModelObject(value[key]);
      if (!rendered) return "";
      return `${humanLabel(key)}\n${rendered}`;
    })
    .filter(Boolean)
    .join("\n\n");
}

function humanLabel(key) {
  const labels = {
    summary: "摘要",
    generated_text: "生成内容",
    scenario: "情境",
    written_scenario: "文字情境",
    visual_brief: "视觉说明",
    semantic_summary: "语义描述",
    discussion_questions: "讨论问题",
    source_trace: "来源线索",
    raw_text: "文本",
  };
  if (labels[key]) return labels[key];
  return String(key)
    .replaceAll("_", " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function stripTextArtifacts(text) {
  let cleaned = String(text)
    .replace(/^```(?:json|markdown|md)?/i, "")
    .replace(/```$/g, "")
    .replace(/^\s{0,3}#{1,6}\s+/gm, "")
    .replace(/\*\*(.*?)\*\*/g, "$1")
    .replace(/__(.*?)__/g, "$1")
    .replace(/^\s*[-*+]\s+/gm, "")
    .replace(/\\n/g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
  if (cleaned.startsWith("{") || cleaned.includes('"summary"') || cleaned.includes('"generated_text"')) {
    cleaned = cleaned
      .replace(/^\s*\{+/, "")
      .replace(/\}+\s*$/, "")
      .replace(/^\s*"([^"]+)"\s*:\s*/gm, (_, key) => `${humanLabel(key)}\n`)
      .replace(/,\s*$/gm, "")
      .replace(/^\s*"\s*/gm, "")
      .replace(/"\s*$/gm, "")
      .replace(/\\"/g, '"')
      .replace(/\n{3,}/g, "\n\n")
      .trim();
  }
  return cleaned;
}

async function createEdge(sourceNodeId, targetNodeId) {
  if (!activeProject || !sourceNodeId || !targetNodeId || sourceNodeId === targetNodeId) return;
  const targetNode = findNode(targetNodeId);
  const targetPort = targetNode?.type === "operation"
    ? (targetNode.config?.definition?.input_ports?.[0]?.id || "in")
    : "in";
  await requestJson(`/api/projects/${activeProject.id}/edges`, {
    method: "POST",
    body: JSON.stringify(withExpectedRevision({
      source_node_id: sourceNodeId,
      target_node_id: targetNodeId,
      source_port: "out",
      target_port: targetPort,
      edge_kind: "data",
      session_id: activeSessionId,
    })),
  });
  await loadCanvas();
}

async function runNode(event, node) {
  event.stopPropagation();
  if (!requireTabApiKey()) return;
  setStatus(canvasStatus, "running");
  const trigger = event.currentTarget;
  const originalLabel = trigger.textContent;
  trigger.disabled = true;
  trigger.classList.add("is-running");
  trigger.setAttribute("aria-busy", "true");
  trigger.setAttribute("aria-label", t("generate.aria"));
  trigger.innerHTML = `<span class="run-spinner" aria-hidden="true"></span><span>${t("common.running")}</span>`;
  try {
    await requestJson(`/api/projects/${activeProject.id}/nodes/${node.id}/run`, {
      method: "POST",
      body: JSON.stringify(withExpectedRevision({ session_id: activeSessionId })),
      requiresApiKey: true,
    });
    await loadCanvas();
  } catch (error) {
    setStatus(canvasStatus, "error");
    canvasOutput.textContent = error.message;
  } finally {
    trigger.disabled = false;
    trigger.classList.remove("is-running");
    trigger.removeAttribute("aria-busy");
    trigger.removeAttribute("aria-label");
    if (trigger.isConnected) trigger.textContent = originalLabel;
  }
}

async function updateNodePayload(node, payload) {
  await requestJson(`/api/projects/${activeProject.id}/nodes/${node.id}`, {
    method: "PATCH",
    body: JSON.stringify(withExpectedRevision({ payload, status: "ready", session_id: activeSessionId })),
  });
  await loadCanvas();
}

function beginDrag(event, node) {
  if (event.button !== 0) return;
  if (event.target.closest("[data-port-role]")) return;
  if (event.target.closest("button, textarea, input, select, label, [contenteditable='true']")) return;
  dragState = {
    node,
    pointerId: event.pointerId,
    startX: event.clientX,
    startY: event.clientY,
    originX: node.position.x,
    originY: node.position.y,
  };
  event.currentTarget.setPointerCapture(event.pointerId);
}

function beginConnection(event, node, nodeElement) {
  if (event.button !== 0) return;
  event.stopPropagation();
  connectionDraft = {
    sourceNodeId: node.id,
    start: portPoint(nodeElement, "out"),
    current: pointInPlane(event),
  };
  event.currentTarget.setPointerCapture(event.pointerId);
  renderEdges();
}

function pointInPlane(event) {
  const rect = canvasPlane.getBoundingClientRect();
  return {
    x: (event.clientX - rect.left) / zoom,
    y: (event.clientY - rect.top) / zoom,
  };
}

window.addEventListener("pointermove", (event) => {
  if (panState) {
    workspace.scrollLeft = panState.originScrollLeft - (event.clientX - panState.startX);
    workspace.scrollTop = panState.originScrollTop - (event.clientY - panState.startY);
    return;
  }
  if (connectionDraft) {
    connectionDraft.current = pointInPlane(event);
    renderEdges();
    return;
  }
  if (!dragState) return;
  const node = dragState.node;
  node.position = {
    x: Math.max(0, dragState.originX + (event.clientX - dragState.startX) / zoom),
    y: Math.max(0, dragState.originY + (event.clientY - dragState.startY) / zoom),
  };
  const element = nodesLayer.querySelector(`[data-node-id="${cssEscape(node.id)}"]`);
  if (element) {
    element.style.left = `${node.position.x}px`;
    element.style.top = `${node.position.y}px`;
  }
  renderPlane();
});

window.addEventListener("pointerup", async (event) => {
  if (panState) {
    panState = null;
    workspace.classList.remove("panning");
    return;
  }
  if (connectionDraft) {
    const target = document.elementFromPoint(event.clientX, event.clientY);
    const inputPort = target?.closest?.('[data-port-role="in"]');
    const targetNode = inputPort?.closest?.(".node");
    const sourceNodeId = connectionDraft.sourceNodeId;
    connectionDraft = null;
    renderEdges();
    if (targetNode?.dataset.nodeId && targetNode.dataset.nodeId !== sourceNodeId) {
      await createEdge(sourceNodeId, targetNode.dataset.nodeId);
    }
    return;
  }
  if (!dragState) return;
  const node = dragState.node;
  dragState = null;
  await requestJson(`/api/projects/${activeProject.id}/nodes/${node.id}`, {
    method: "PATCH",
    body: JSON.stringify(withExpectedRevision({ position: node.position, session_id: activeSessionId })),
  });
});

function backHome() {
  closeNodeMenu();
  closeTextReader();
  window.clearTimeout(autosaveTimer);
  canvas.classList.remove("active");
  home.classList.remove("hidden");
  activeProject = null;
  activeCanvas = null;
  activeInteraction = null;
  activeProjection = null;
  activeSessionId = null;
  activeScopeId = null;
  previewFocusedStageId = "";
}

async function deleteProject(project) {
  if (!project) return;
  const confirmed = window.confirm(t("project.deleteConfirm", { title: project.title }));
  if (!confirmed) return;
  await requestJson(`/api/projects/${project.id}`, { method: "DELETE" });
  if (activeProject?.id === project.id) backHome();
  await loadProjects();
}

async function setZoom(nextZoom, anchorEvent = null) {
  const previousZoom = zoom;
  const next = clampZoom(nextZoom);
  if (next === previousZoom) {
    updateZoomControls();
    return;
  }
  const anchor = anchorEvent ? zoomAnchor(anchorEvent, previousZoom) : null;
  zoom = next;
  if (activeCanvas) {
    activeCanvas.viewport = { ...(activeCanvas.viewport || {}), zoom };
  }
  renderPlane();
  scheduleViewportAutosave();
  if (anchor) {
    workspace.scrollLeft = anchor.planeX * zoom - anchor.offsetX;
    workspace.scrollTop = anchor.planeY * zoom - anchor.offsetY;
  }
}

function clampZoom(value) {
  return Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, Number(value) || MAX_ZOOM));
}

function zoomAnchor(event, currentZoom) {
  const rect = workspace.getBoundingClientRect();
  const offsetX = event.clientX - rect.left;
  const offsetY = event.clientY - rect.top;
  return {
    offsetX,
    offsetY,
    planeX: (workspace.scrollLeft + offsetX) / currentZoom,
    planeY: (workspace.scrollTop + offsetY) / currentZoom,
  };
}

function handleWheelZoom(event) {
  if (!activeCanvas) return;
  event.preventDefault();
  if (event.ctrlKey || event.metaKey || event.altKey) {
    const factor = Math.exp(-event.deltaY * 0.002);
    setZoom(zoom * factor, event);
    return;
  }
  workspace.scrollLeft += event.deltaX;
  workspace.scrollTop += event.deltaY;
  closeNodeMenu();
}

function beginCanvasPan(event) {
  if (!activeCanvas) return;
  if (event.target.closest(".node, button, input, textarea, label")) return;
  if (event.button !== 1 && !(event.button === 0 && spacePressed)) return;
  event.preventDefault();
  panState = {
    startX: event.clientX,
    startY: event.clientY,
    originScrollLeft: workspace.scrollLeft,
    originScrollTop: workspace.scrollTop,
  };
  workspace.classList.add("panning");
}

function applyTheme(theme) {
  const nextTheme = theme === "dark" ? "dark" : "light";
  document.documentElement.dataset.theme = nextTheme;
  themeToggles.forEach((button) => {
    button.textContent = nextTheme === "dark" ? t("theme.light") : t("theme.dark");
    button.setAttribute("aria-pressed", String(nextTheme === "dark"));
  });
  localStorage.setItem(THEME_KEY, nextTheme);
}

function toggleTheme() {
  applyTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark");
}

function updateZoomControls() {
  zoomLevel.textContent = `${Math.round(zoom * 100)}%`;
  zoomOut.disabled = zoom <= MIN_ZOOM;
  zoomIn.disabled = zoom >= MAX_ZOOM;
}

function titleForType(type) {
  return {
    text: t("nodes.textTitle"),
    conversation: t("nodes.conversationTitle"),
    upload: t("nodes.uploadTitle"),
    image: t("nodes.imageTitle"),
    multimodal: t("nodes.multimodalTitle"),
    modify: t("nodes.modifyTitle"),
    operation: t("nodes.operationTitle"),
  }[type];
}

function defaultTextForType(type) {
  return {
    text: t("nodes.textDefault"),
    conversation: t("nodes.conversationDefault"),
    upload: "",
    image: t("nodes.imageDefault"),
    modify: "",
    operation: t("nodes.operationDefault"),
  }[type];
}

function cssEscape(value) {
  if (window.CSS?.escape) return window.CSS.escape(value);
  return String(value).replaceAll('"', '\\"');
}

function exportCurrentCanvasPdf() {
  if (!activeProject || !activeCanvas) return;
  const reportWindow = window.open("", "_blank");
  if (!reportWindow) {
    window.alert(locale === "zh" ? "浏览器阻止了导出窗口，请允许弹窗后重试。" : "The browser blocked the export window. Allow pop-ups and try again.");
    return;
  }
  const generatedAt = new Date().toLocaleString(locale === "zh" ? "zh-CN" : "en-US");
  const session = activeSession();
  const title = activeProject.title || activeCanvas.id || t("export.title");
  const cardsMarkup = stagePresentation?.innerHTML?.trim()
    ? stagePresentation.innerHTML
    : `<p class="report-empty">${escapeHtml(t("workflowStrip.empty"))}</p>`;
  const nodeMarkup = printableNodeReport();
  const chatMarkup = printableChatReport(session);
  const stylesheet = `/static/styles.css?v=20260804-performance-cache`;
  reportWindow.document.open();
  reportWindow.document.write(`<!doctype html>
<html lang="${locale === "zh" ? "zh-CN" : "en"}">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>${escapeHtml(title)} · ${escapeHtml(t("common.exportPdf"))}</title>
  <link rel="stylesheet" href="${stylesheet}" />
  <style>
    body { margin: 0; background: #ffffff; color: #15191d; font-family: "Heiti SC", "PingFang SC", "Microsoft YaHei", Arial, sans-serif; }
    .report { max-width: 1120px; margin: 0 auto; padding: 30px; }
    .report-header { display: flex; justify-content: space-between; gap: 20px; border-bottom: 2px solid #15191d; padding-bottom: 14px; }
    .report-header h1 { margin: 0; font-size: 24px; font-weight: 900; }
    .report-header p { margin: 6px 0 0; color: #596168; font-size: 12px; }
    .report-section { break-inside: avoid; margin-top: 26px; }
    .report-section h2 { margin: 0 0 12px; color: #f02a0c; font-size: 15px; font-weight: 900; text-transform: uppercase; }
    .report-print-hint { color: #596168; font-size: 11px; }
    .stage-presentation, .stage-deck, .foundation-start-deck { max-height: none !important; overflow: visible !important; }
    .stage-deck, .foundation-start-deck, .report-node-grid { display: grid !important; grid-template-columns: repeat(2, minmax(0, 1fr)) !important; gap: 12px !important; }
    .stage-deck-card, .foundation-start-card, .report-node, .report-message { break-inside: avoid; border: 1px solid rgba(20, 24, 28, 0.16) !important; border-radius: 8px !important; background: #fff !important; color: #15191d !important; box-shadow: none !important; }
    .stage-deck-card, .foundation-start-card { min-height: 0 !important; padding: 10px !important; }
    .stage-deck-header { pointer-events: none; }
    button { color: inherit; }
    .report-node { padding: 12px; }
    .report-node header { display: flex; justify-content: space-between; gap: 12px; margin-bottom: 8px; color: #f02a0c; font-size: 11px; font-weight: 900; }
    .report-node h3 { margin: 0 0 8px; font-size: 14px; }
    .report-node p, .report-message p { margin: 0; white-space: pre-wrap; font-size: 11.5px; line-height: 1.5; }
    .report-node img { display: block; width: 100%; max-height: 170px; object-fit: cover; border-radius: 6px; margin: 8px 0; }
    .report-chat { display: grid; gap: 8px; }
    .report-message { padding: 10px 12px; }
    .report-message strong { display: block; margin-bottom: 5px; color: #f02a0c; font-size: 11px; }
    .report-message small { display: block; margin-top: 5px; color: #737980; font-size: 10px; }
    .report-empty { color: #737980; font-size: 12px; }
    @media print {
      @page { size: A4; margin: 12mm; }
      .report { max-width: none; padding: 0; }
      .report-print-hint { display: none; }
      .report-section { page-break-inside: avoid; }
    }
  </style>
</head>
<body>
  <main class="report">
    <header class="report-header">
      <div>
        <h1>${escapeHtml(title)}</h1>
        <p>${escapeHtml(t("export.title"))}</p>
      </div>
      <div>
        <p>${escapeHtml(t("export.generatedAt"))}: ${escapeHtml(generatedAt)}</p>
        <p>r${escapeHtml(activeCanvas.revision ?? 0)} · ${escapeHtml(activeCanvas.nodes.length)} nodes</p>
      </div>
    </header>
    <p class="report-print-hint">${escapeHtml(t("export.printHint"))}</p>
    <section class="report-section">
      <h2>${escapeHtml(t("export.cards"))}</h2>
      <div class="stage-presentation">${cardsMarkup}</div>
    </section>
    <section class="report-section">
      <h2>${escapeHtml(t("export.canvasNodes"))}</h2>
      ${nodeMarkup}
    </section>
    <section class="report-section">
      <h2>${escapeHtml(t("export.chat"))}</h2>
      ${chatMarkup}
    </section>
  </main>
  <script>
    window.addEventListener("load", () => {
      setTimeout(() => window.print(), 250);
    });
  </script>
</body>
</html>`);
  reportWindow.document.close();
}

function printableNodeReport() {
  const nodes = activeCanvas?.nodes || [];
  if (!nodes.length) return `<p class="report-empty">${escapeHtml(t("navigator.none"))}</p>`;
  return `<div class="report-node-grid">${nodes.map((node) => {
    const text = plainTextForNode(node) || node.payload?.semantic_summary || node.payload?.filename || "";
    const imageUrl = node.payload?.image_url || "";
    return `<article class="report-node">
      <header><span>${escapeHtml(nodeTypeLabel(node.type))}</span><span>${escapeHtml(statusLabel(node.status || "draft"))}</span></header>
      <h3>${escapeHtml(localizedReferenceTitle(node.title || node.id))}</h3>
      ${imageUrl ? `<img src="${escapeHtml(imageUrl)}" alt="${escapeHtml(localizedReferenceTitle(node.title || ""))}" />` : ""}
      <p>${escapeHtml(stripTextArtifacts(text || node.payload?.text || ""))}</p>
    </article>`;
  }).join("")}</div>`;
}

function printableChatReport(session) {
  const messages = (session?.messages || []).filter((message) => !(message.role === "system" && message.kind !== "activity"));
  if (!messages.length) return `<p class="report-empty">${escapeHtml(t("export.noMessages"))}</p>`;
  return `<div class="report-chat">${messages.map((message) => {
    const perspective = message.input_perspective
      ? ` · ${t(message.input_perspective === "design" ? "conversation.designerInput" : "conversation.scientistInput")}`
      : "";
    const role = `${t(`conversation.${message.role}`)}${perspective}`;
    return `<article class="report-message">
      <strong>${escapeHtml(role)}</strong>
      <p>${escapeHtml(localizedConversationBody(message.body || ""))}</p>
      ${message.created_at ? `<small>${escapeHtml(message.created_at)}</small>` : ""}
    </article>`;
  }).join("")}</div>`;
}

window.addEventListener("resize", renderPlane);
zoomOut.addEventListener("click", () => setZoom(zoom - ZOOM_STEP));
zoomIn.addEventListener("click", () => setZoom(zoom + ZOOM_STEP));
exportPdfButton?.addEventListener("click", exportCurrentCanvasPdf);
workspace.addEventListener("wheel", handleWheelZoom, { passive: false });
workspace.addEventListener("pointerdown", beginCanvasPan);
themeToggles.forEach((button) => button.addEventListener("click", toggleTheme));
document.querySelectorAll("[data-language-toggle]").forEach((button) => {
  button.addEventListener("click", () => applyLocale(locale === "zh" ? "en" : "zh"));
});
menuOpenFull.addEventListener("click", openContextNodeText);
menuDelete.addEventListener("click", () => {
  deleteContextNode().catch((error) => {
    setStatus(canvasStatus, "error");
    canvasOutput.textContent = error.message;
  });
});
closeReader.addEventListener("click", closeTextReader);
textReader.addEventListener("click", (event) => {
  if (event.target === textReader) closeTextReader();
});
closeImageViewerButton.addEventListener("click", closeImageViewer);
imageViewer.addEventListener("click", (event) => {
  if (event.target === imageViewer) closeImageViewer();
});
document.addEventListener("click", (event) => {
  if (!event.target.closest("#node-menu")) closeNodeMenu();
});
document.addEventListener("keydown", (event) => {
  if (event.code === "Space" && !event.target.closest?.("textarea, input")) {
    spacePressed = true;
    workspace.classList.add("pan-ready");
  }
  if (event.key === "Escape") {
    closeNodeMenu();
    closeTextReader();
    closeImageViewer();
    closeCanvasFocus();
  }
});
document.addEventListener("keyup", (event) => {
  if (event.code === "Space") {
    spacePressed = false;
    workspace.classList.remove("pan-ready");
  }
});
workspace.addEventListener("scroll", closeNodeMenu);
workspace.addEventListener("scroll", scheduleViewportAutosave);

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function compactConversationText(value, limit = 200) {
  const body = String(value ?? "").trim();
  if (body.length <= limit) return body;
  return `${body.slice(0, Math.max(0, limit - 1)).trimEnd()}…`;
}

function loadAgentGuideCache() {
  try {
    const raw = window.sessionStorage?.getItem(AGENT_GUIDE_CACHE_KEY);
    if (!raw) return new Map();
    const parsed = JSON.parse(raw);
    return new Map(Array.isArray(parsed) ? parsed.slice(-60) : []);
  } catch {
    return new Map();
  }
}

function rememberAgentGuide(key, payload) {
  agentGuideCache.set(key, payload);
  try {
    const entries = [...agentGuideCache.entries()].slice(-60);
    window.sessionStorage?.setItem(AGENT_GUIDE_CACHE_KEY, JSON.stringify(entries));
  } catch {
    // Cache is an optimization only; the deterministic guide remains available.
  }
}

function compactAgentValue(value, limit = 360) {
  if (Array.isArray(value)) return value.map((item) => compactConversationText(item, 120)).filter(Boolean).slice(0, 5);
  if (value && typeof value === "object") return compactAgentValue(JSON.stringify(value), limit);
  return compactConversationText(value || "", limit);
}

function compactBriefForAgent(brief = {}) {
  return {
    start_mode: brief.start_mode || "research",
    topic: compactAgentValue(brief.topic, 220),
    research_focus: compactAgentValue(brief.research_focus, 420),
    assumptions: compactAgentValue(brief.assumptions, 160),
    stakeholders: compactAgentValue(brief.stakeholders, 160),
    tensions: compactAgentValue(brief.tensions, 180),
  };
}

createForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const title = document.querySelector("#project-title").value;
  const { project } = await requestJson("/api/projects", {
    method: "POST",
    body: JSON.stringify({ title }),
  });
  await loadProjects();
  openCanvas(project);
});

document.querySelector("#back-home").addEventListener("click", backHome);
deleteActiveProject.addEventListener("click", () => {
  deleteProject(activeProject).catch((error) => {
    setStatus(canvasStatus, "error");
    canvasOutput.textContent = error.message;
  });
});
canvasTitle.addEventListener("dblclick", () => {
  renameProject().catch((error) => {
    setStatus(canvasStatus, "error");
    canvasOutput.textContent = error.message;
  });
});
document.querySelectorAll("[data-add-node]").forEach((button) => {
  button.addEventListener("click", () => addNode(button.dataset.addNode));
});

document.querySelectorAll("[data-add-operation-definition]").forEach((button) => {
  button.addEventListener("click", () => addNode("operation", {
    title: "",
    config: { definition_ref: { id: button.dataset.addOperationDefinition } },
  }));
});


conversationForm.addEventListener("submit", (event) => {
  event.preventDefault();
  runUiAction(() => submitConversationMessage(event));
});

openCanvasFocusButton?.addEventListener("click", openCanvasFocus);
openCanvasFocusButton?.addEventListener("keydown", (event) => {
  if (event.key !== "Enter" && event.key !== " ") return;
  event.preventDefault();
  openCanvasFocus();
});
closeCanvasFocusButton.addEventListener("click", closeCanvasFocus);

returnLocalScope.addEventListener("click", () => {
  setActiveScope(defaultLocalScopeId());
});

apiAccessForm.addEventListener("submit", acceptTabApiKey);

conversationPerspectiveButtons.forEach((button) => {
  button.addEventListener("click", async () => {
    const nextMode = button.dataset.conversationPerspective === "design" ? "design" : "research";
    conversationPerspective = nextMode;
    renderConversationPerspective(activeSession());
    const session = activeSession();
    if (session?.guide?.stage_id === "start" && !session?.guide?.workflow_instance_id) {
      await runUiAction(() => advanceConversationGuide({ action: "set_start_mode", start_mode: nextMode }));
    } else {
      conversationInput?.focus();
    }
  });
});

imageFile?.addEventListener("change", () => {
  imageFileName.textContent = imageFile.files[0]?.name || t("common.noFile");
});

paperFile?.addEventListener("change", () => {
  paperFileName.textContent = paperFile.files[0]?.name || t("common.noFile");
});

function clearDocumentInputs() {
  if (imageFile) imageFile.value = "";
  if (paperFile) paperFile.value = "";
  if (imageFileName) imageFileName.textContent = t("common.noFile");
  if (paperFileName) paperFileName.textContent = t("common.noFile");
  documentOutput.textContent = "";
  setStatus(documentStatus, "idle");
}

function selectedPaperPdf() {
  return paperFile?.files?.[0] || null;
}

function selectedImageInput() {
  return imageFile?.files?.[0] || null;
}

function compactDocumentSummary(documentPayload = {}) {
  const zh = locale === "zh";
  const lines = [
    `${zh ? "文件" : "File"}: ${documentPayload.filename || ""}`,
    `${zh ? "类型" : "Type"}: ${documentPayload.kind || documentPayload.type || ""}`,
  ];
  if (documentPayload.page_count) lines.push(`${zh ? "页数" : "Pages"}: ${documentPayload.page_count}`);
  if (documentPayload.characters) lines.push(`${zh ? "可读字符" : "Readable characters"}: ${documentPayload.characters}`);
  if (documentPayload.preview) lines.push("", zh ? "内容预览:" : "Preview:", compactConversationText(documentPayload.preview, 520));
  return lines.filter((line) => line !== undefined).join("\n").trim();
}

function compactPaperImportSummary(paper = {}) {
  const zh = locale === "zh";
  const brief = paper.paper_brief || {};
  const document = brief.import_document || {};
  const keywords = Array.isArray(document.keywords) ? document.keywords.join("、") : "";
  const lines = [
    zh ? "已导入论文并自动填写第一步研究议题卡片。" : "Paper imported and first-step research inquiry cards were filled.",
    `${zh ? "文件" : "File"}: ${paper.filename || document.filename || ""}`,
    `${zh ? "页数" : "Pages"}: ${paper.page_count || document.page_count || ""}`,
    `${zh ? "研究议题" : "Research topic"}: ${brief.topic || ""}`,
    `${zh ? "研究关注点" : "Research focus"}: ${compactConversationText(brief.research_focus || "", 360)}`,
  ];
  if (keywords) lines.push(`${zh ? "关键词" : "Keywords"}: ${keywords}`);
  if (paper.preview) lines.push("", zh ? "论文摘要预览:" : "Paper preview:", compactConversationText(paper.preview, 520));
  return lines.filter((line) => String(line || "").trim()).join("\n");
}

async function addImageInputNodeFromFile(file) {
  const formData = new FormData();
  formData.append("file", file);
  const result = await requestJson("/api/images/upload", {
    method: "POST",
    body: formData,
  });
  const image = result.image || {};
  await requestJson(`/api/projects/${activeProject.id}/nodes`, {
    method: "POST",
    body: JSON.stringify(withExpectedRevision({
      type: "image",
      title: image.filename || file.name,
      position: { x: 96 + (activeCanvas?.nodes?.length || 0) * 24, y: 116 + (activeCanvas?.nodes?.length || 0) * 24 },
      payload: {
        filename: image.filename || file.name,
        mime_type: image.mime_type || file.type,
        image_file: image.image_file || "",
        image_url: image.image_url || "",
        image_source: "upload",
        semantic_status: "available for visual reasoning",
        text: `${t("node.imageReference")}: ${image.filename || file.name}`,
      },
      status: "ready",
      session_id: activeSessionId,
    })),
  });
  return image;
}

clearDocumentInputsButton?.addEventListener("click", clearDocumentInputs);

undoCurrentStepButton?.addEventListener("click", async () => {
  if (!activeProject) return;
  if (!window.confirm(t("workflow.undoStepConfirm"))) return;
  undoCurrentStepButton.disabled = true;
  setStatus(documentStatus, "loading");
  try {
    const result = await requestJson(`/api/projects/${activeProject.id}/workflow-step-reset`, {
      method: "POST",
      body: JSON.stringify(withExpectedRevision({ session_id: activeSessionId })),
    });
    if (result.conversation?.id) activeSessionId = result.conversation.id;
    activeScopeId = result.conversation?.active_scope_id || "scope-global";
    clearDocumentInputs();
    documentOutput.textContent = t("workflow.undoStepDone");
    setStatus(documentStatus, "ready");
    await loadCanvas({ preserveView: false });
  } catch (error) {
    setStatus(documentStatus, "error");
    documentOutput.textContent = error.message;
  } finally {
    undoCurrentStepButton.disabled = false;
  }
});

importPaperButton?.addEventListener("click", async () => {
  const file = selectedPaperPdf();
  if (!activeProject || !file) return;
  if (!file.name.toLowerCase().endsWith(".pdf")) {
    setStatus(documentStatus, "error");
    documentOutput.textContent = t("document.onlyPaperPdf");
    return;
  }
  setStatus(documentStatus, "importing");
  importPaperButton.disabled = true;
  const formData = new FormData();
  formData.append("file", file);
  if (activeSessionId) formData.append("session_id", activeSessionId);
  const revision = activeInteraction?.revision ?? activeCanvas?.revision;
  if (Number.isInteger(revision)) formData.append("expected_revision", String(revision));
  try {
    const result = await requestJson(`/api/projects/${activeProject.id}/paper-import`, {
      method: "POST",
      body: formData,
    });
    const paper = result.paper || {};
    if (result.conversation?.id) activeSessionId = result.conversation.id;
    if (result.conversation?.active_scope_id) activeScopeId = result.conversation.active_scope_id;
    setStatus(documentStatus, "ready");
    documentOutput.textContent = compactPaperImportSummary(paper);
    await loadCanvas({ preserveView: false });
  } catch (error) {
    setStatus(documentStatus, "error");
    documentOutput.textContent = error.message;
  } finally {
    importPaperButton.disabled = false;
  }
});

documentForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const image = selectedImageInput();
  const paper = selectedPaperPdf();
  if (!image && !paper) {
    setStatus(documentStatus, "error");
    documentOutput.textContent = t("document.noReadableFile");
    return;
  }
  setStatus(documentStatus, "reading");
  const summaries = [];
  try {
    if (image) {
      const uploaded = await addImageInputNodeFromFile(image);
      summaries.push(`${t("document.imageImported")}\n${uploaded.filename || image.name}`);
      await loadCanvas({ preserveView: true });
    }
    if (paper) {
      const formData = new FormData();
      formData.append("file", paper);
      const result = await requestJson("/api/documents/inspect", {
        method: "POST",
        body: formData,
      });
      summaries.push(compactDocumentSummary(result.document || {}));
    }
    setStatus(documentStatus, "ready");
    documentOutput.textContent = summaries.join("\n\n");
  } catch (error) {
    setStatus(documentStatus, "error");
    documentOutput.textContent = error.message;
  }
});

applyLocale(locale);
loadModelStatus()
  .then(() => {
    setApiAccessState(!hasServerModelAccess() && !tabApiKey);
  })
  .catch(() => {
    setApiAccessState(true);
  });
