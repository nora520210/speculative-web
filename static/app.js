const home = document.querySelector(".home");
const canvas = document.querySelector(".canvas-shell");
const projectsEl = document.querySelector("#projects");
const projectCount = document.querySelector("#project-count");
const canvasTitle = document.querySelector("#canvas-title");
const createForm = document.querySelector("#create-project");
const deleteActiveProject = document.querySelector("#delete-active-project");
const documentForm = document.querySelector("#document-form");
const documentFile = document.querySelector("#document-file");
const documentFileName = document.querySelector("#document-file-name");
const documentOutput = document.querySelector("#document-output");
const documentStatus = document.querySelector("#document-status");
const canvasStatus = document.querySelector("#canvas-status");
const canvasOutput = document.querySelector("#canvas-output");
const modelStatus = document.querySelector("#model-status");
const modelOutput = document.querySelector("#model-output");
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

let activeProject = null;
let activeCanvas = null;
let dragState = null;
let connectionDraft = null;
let panState = null;
let contextNodeId = null;
let contextEdgeId = null;
let zoom = 1;
let spacePressed = false;
let tabApiKey = "";
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
    "common.noFile": "No file selected",
    "common.read": "Read",
    "common.open": "Open",
    "common.delete": "Delete",
    "common.close": "Close",
    "common.run": "Run",
    "common.running": "Running",
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
    "nodes.textTitle": "Text Node",
    "nodes.conversationTitle": "Conversation",
    "nodes.uploadTitle": "Upload",
    "nodes.imageTitle": "Image Node",
    "nodes.multimodalTitle": "Text+Image Node",
    "nodes.modifyTitle": "Modify",
    "nodes.textDefault": "New text information node.",
    "nodes.conversationDefault": "Conversation or intermediate thinking content.",
    "nodes.imageDefault": "Image semantic summary placeholder.",
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
    "status.running": "running",
    "status.deleting": "deleting",
    "status.error": "error",
    "status.draft": "draft",
    "status.success": "success",
    "status.failed": "failed",
    "status.stale": "stale",
    "status.generated": "generated",
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
    "common.noFile": "未选择文件",
    "common.read": "读取",
    "common.open": "打开",
    "common.delete": "删除",
    "common.close": "关闭",
    "common.run": "运行",
    "common.running": "生成中",
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
    "nodes.textTitle": "文本节点",
    "nodes.conversationTitle": "对话",
    "nodes.uploadTitle": "上传",
    "nodes.imageTitle": "图像节点",
    "nodes.multimodalTitle": "图文节点",
    "nodes.modifyTitle": "推演",
    "nodes.textDefault": "新的文本信息节点。",
    "nodes.conversationDefault": "对话或中间思考内容。",
    "nodes.imageDefault": "图像语义摘要占位。",
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
    "status.running": "生成中",
    "status.deleting": "删除中",
    "status.error": "错误",
    "status.draft": "草稿",
    "status.success": "完成",
    "status.failed": "失败",
    "status.stale": "待更新",
    "status.generated": "已生成",
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

function statusLabel(value) {
  const key = String(value || "draft").toLowerCase();
  return translations[locale]?.[`status.${key}`] ? t(`status.${key}`) : key;
}

function nodeTypeLabel(type) {
  return translations[locale]?.[`nodes.${type}`] ? t(`nodes.${type}`) : type;
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
  document.querySelectorAll("[data-language-toggle]").forEach((button) => {
    const targetLanguage = locale === "zh" ? "EN" : "中文";
    button.textContent = targetLanguage;
    button.setAttribute("aria-label", locale === "zh" ? "Switch to English" : "切换至中文");
  });
  localStorage.setItem(LOCALE_KEY, locale);
  applyTheme(document.documentElement.dataset.theme || "light");
  if (activeProject) {
    updateCanvasTitle(activeProject.title);
    renderCanvas();
  }
  loadProjects().catch((error) => {
    projectsEl.textContent = error.message;
  });
}

async function requestJson(url, options = {}) {
  const { requiresApiKey = false, headers: optionHeaders = {}, ...requestOptions } = options;
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
    throw new Error(payload.error || `Request failed: ${response.status}`);
  }
  return payload;
}

function requireTabApiKey() {
  if (tabApiKey) return true;
  apiAccessError.textContent = t("access.required");
  setApiAccessState(true);
  apiAccessKey.focus();
  return false;
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

async function loadCanvas({ preserveView = true } = {}) {
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
  setStatus(canvasStatus, "ready");
  canvasOutput.textContent = JSON.stringify(summarizeCanvas(graph), null, 2);
  renderCanvas();
  if (shouldPreserveView) restoreCanvasView(previousView);
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
  if (tabApiKey) {
    setStatus(modelStatus, "ready");
    modelOutput.textContent = t("access.active");
    return;
  }
  setStatus(modelStatus, model.openai_api_key_configured ? "configured" : "offline");
  modelOutput.textContent = JSON.stringify(model, null, 2);
}

function renderCanvas() {
  if (!activeCanvas) return;
  nodesLayer.innerHTML = "";
  for (const node of activeCanvas.nodes) {
    nodesLayer.append(renderNode(node));
  }
  requestAnimationFrame(renderPlane);
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
  if (!activeCanvas) return;
  edgesLayer.innerHTML = "";
  edgesLayer.setAttribute("width", String(size.width));
  edgesLayer.setAttribute("height", String(size.height));
  edgesLayer.removeAttribute("viewBox");

  for (const edge of activeCanvas.edges) {
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
  const nodes = activeCanvas?.nodes || [];
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
  hit.addEventListener("contextmenu", (event) => openEdgeMenu(event, edge));
  group.addEventListener("contextmenu", (event) => openEdgeMenu(event, edge));
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
      <span>${escapeHtml(node.title)}</span>
      <span>${escapeHtml(node.active_run_id || "revision 1")}</span>
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
  const runButton = article.querySelector("[data-run-modify]");
  if (runButton) {
    runButton.addEventListener("click", (event) => runModify(event, node));
  }
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
    const tools = node.config?.tools || [];
    const outputType = node.config?.output_type || "text";
    const recommendation = outputRecommendation(node);
    const toolRows = tools
      .map(
        (tool) => `
          <button class="tool-row ${tool.selected ? "selected" : ""}" type="button" data-tool-id="${escapeHtml(tool.id)}">
            <span class="dot"></span><span>${escapeHtml(tool.label)}</span>
            ${tool.description ? `<span class="tool-tooltip" role="tooltip">${escapeHtml(tool.description)}</span>` : ""}
          </button>
        `,
      )
      .join("");
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
      <div class="tool-stack">${toolRows}</div>
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
    <textarea aria-label="${escapeHtml(node.title)}">${escapeHtml(node.payload?.text || "")}</textarea>
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
          <span class="recommendation-tool">${escapeHtml(item.label)}</span>
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

async function addNode(type) {
  if (!activeProject || !activeCanvas) return;
  const offset = activeCanvas.nodes.length * 24;
  const payload = {
    type,
    title: titleForType(type),
    position: { x: 92 + offset, y: 110 + offset },
    payload: { text: defaultTextForType(type) },
  };
  await requestJson(`/api/projects/${activeProject.id}/nodes`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
  await loadCanvas();
}

async function toggleTool(event, node) {
  event.stopPropagation();
  const toolId = event.currentTarget.dataset.toolId;
  const tools = node.config.tools.map((tool) =>
    tool.id === toolId ? { ...tool, selected: !tool.selected } : tool,
  );
  await requestJson(`/api/projects/${activeProject.id}/nodes/${node.id}`, {
    method: "PATCH",
    body: JSON.stringify({ config: { tools } }),
  });
  await loadCanvas();
}

async function setOutputType(event, node) {
  event.stopPropagation();
  const outputType = event.currentTarget.dataset.outputType;
  await requestJson(`/api/projects/${activeProject.id}/nodes/${node.id}`, {
    method: "PATCH",
    body: JSON.stringify({ config: { output_type: outputType } }),
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
  });
  await loadCanvas();
}

function openContextNodeText() {
  const node = findNode(contextNodeId);
  closeNodeMenu();
  if (node) openTextReader(node);
}

function openTextReader(node) {
  textReaderTitle.textContent = node.title || node.type || t("reader.nodeText");
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
  imageViewerTitle.textContent = node.title || t("reader.imagePreview");
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
  await requestJson(`/api/projects/${activeProject.id}/edges`, {
    method: "POST",
    body: JSON.stringify({
      source_node_id: sourceNodeId,
      target_node_id: targetNodeId,
      source_port: "out",
      target_port: "in",
      edge_kind: "data",
    }),
  });
  await loadCanvas();
}

async function runModify(event, node) {
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
      body: JSON.stringify({}),
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
    body: JSON.stringify({ payload, status: "ready" }),
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
    body: JSON.stringify({ position: node.position }),
  });
});

function backHome() {
  closeNodeMenu();
  closeTextReader();
  canvas.classList.remove("active");
  home.classList.remove("hidden");
  activeProject = null;
  activeCanvas = null;
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
  }[type];
}

function defaultTextForType(type) {
  return {
    text: t("nodes.textDefault"),
    conversation: t("nodes.conversationDefault"),
    upload: "",
    image: t("nodes.imageDefault"),
    modify: "",
  }[type];
}

function cssEscape(value) {
  if (window.CSS?.escape) return window.CSS.escape(value);
  return String(value).replaceAll('"', '\\"');
}

window.addEventListener("resize", renderPlane);
zoomOut.addEventListener("click", () => setZoom(zoom - ZOOM_STEP));
zoomIn.addEventListener("click", () => setZoom(zoom + ZOOM_STEP));
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
  }
});
document.addEventListener("keyup", (event) => {
  if (event.code === "Space") {
    spacePressed = false;
    workspace.classList.remove("pan-ready");
  }
});
workspace.addEventListener("scroll", closeNodeMenu);

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
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

apiAccessForm.addEventListener("submit", acceptTabApiKey);

documentFile.addEventListener("change", () => {
  documentFileName.textContent = documentFile.files[0]?.name || t("common.noFile");
});

documentForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!documentFile.files.length) return;
  setStatus(documentStatus, "reading");
  const formData = new FormData();
  formData.append("file", documentFile.files[0]);
  try {
    const result = await requestJson("/api/documents/inspect", {
      method: "POST",
      body: formData,
    });
    setStatus(documentStatus, "ready");
    documentOutput.textContent = JSON.stringify(result.document, null, 2);
  } catch (error) {
    setStatus(documentStatus, "error");
    documentOutput.textContent = error.message;
  }
});

applyLocale(locale);
setApiAccessState(true);
