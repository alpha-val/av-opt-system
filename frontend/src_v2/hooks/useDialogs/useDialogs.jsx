import * as React from "react";
import PropTypes from "prop-types";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogContentText from "@mui/material/DialogContentText";
import DialogTitle from "@mui/material/DialogTitle";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import Box from "@mui/material/Box";
import useEventCallback from "@mui/utils/useEventCallback";
import DialogsContext from "./DialogsContext";
import DeleteSweep from "@mui/icons-material/DeleteSweep";
import CircularProgress from "@mui/material/CircularProgress";
import Warning from "@mui/icons-material/Warning";

/**
 * The props that are passed to a dialog component.
 */

function useDialogLoadingButton(onClose) {
  const [loading, setLoading] = React.useState(false);
  const handleClick = async () => {
    try {
      setLoading(true);
      await onClose();
    } finally {
      setLoading(false);
    }
  };
  return {
    onClick: handleClick,
    loading,
  };
}

function AlertDialog({ open, payload, onClose }) {
  const okButtonProps = useDialogLoadingButton(() => onClose());

  return (
    <Dialog maxWidth="xs" fullWidth open={open} onClose={() => onClose()}>
      <DialogTitle>{payload.title ?? "Alert"}</DialogTitle>
      <DialogContent>{payload.msg}</DialogContent>
      <DialogActions>
        <Button disabled={!open} {...okButtonProps}>
          {payload.okText ?? "Ok"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

AlertDialog.propTypes = {
  /**
   * A function to call when the dialog should be closed. If the dialog has a return
   * value, it should be passed as an argument to this function. You should use the promise
   * that is returned to show a loading state while the dialog is performing async actions
   * on close.
   * @param result The result to return from the dialog.
   * @returns A promise that resolves when the dialog can be fully closed.
   */
  onClose: PropTypes.func.isRequired,
  /**
   * Whether the dialog is open.
   */
  open: PropTypes.bool.isRequired,
  /**
   * The payload that was passed when the dialog was opened.
   */
  payload: PropTypes.shape({
    msg: PropTypes.node,
    okText: PropTypes.node,
    onClose: PropTypes.func,
    title: PropTypes.node,
  }).isRequired,
};

export { AlertDialog };

function ConfirmDialog({ open, payload, onClose }) {
  const cancelButtonProps = useDialogLoadingButton(() => onClose(false));
  const okButtonProps = useDialogLoadingButton(() => onClose(true));

  return (
    <Dialog maxWidth="xs" fullWidth open={open} onClose={() => onClose(false)}>
      <DialogTitle>{payload.title ?? "Confirm"}</DialogTitle>
      <DialogContent>{payload.msg}</DialogContent>
      <DialogActions>
        <Button autoFocus disabled={!open} {...cancelButtonProps}>
          {payload.cancelText ?? "Cancel"}
        </Button>
        <Button color={payload.severity} disabled={!open} {...okButtonProps}>
          {payload.okText ?? "Ok"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

ConfirmDialog.propTypes = {
  /**
   * A function to call when the dialog should be closed. If the dialog has a return
   * value, it should be passed as an argument to this function. You should use the promise
   * that is returned to show a loading state while the dialog is performing async actions
   * on close.
   * @param result The result to return from the dialog.
   * @returns A promise that resolves when the dialog can be fully closed.
   */
  onClose: PropTypes.func.isRequired,
  /**
   * Whether the dialog is open.
   */
  open: PropTypes.bool.isRequired,
  /**
   * The payload that was passed when the dialog was opened.
   */
  payload: PropTypes.shape({
    cancelText: PropTypes.node,
    msg: PropTypes.node,
    okText: PropTypes.node,
    onClose: PropTypes.func,
    severity: PropTypes.oneOf(["error", "info", "success", "warning"]),
    title: PropTypes.node,
  }).isRequired,
};

export { ConfirmDialog };

function PromptDialog({ open, payload, onClose }) {
  const [input, setInput] = React.useState("");
  const cancelButtonProps = useDialogLoadingButton(() => onClose(null));

  const [loading, setLoading] = React.useState(false);

  const name = "input";
  return (
    <Dialog
      maxWidth="xs"
      fullWidth
      open={open}
      onClose={() => onClose(null)}
      slotProps={{
        paper: {
          component: "form",
          onSubmit: async (event) => {
            event.preventDefault();
            try {
              setLoading(true);
              const formData = new FormData(event.currentTarget);
              const value = formData.get(name) ?? "";

              if (typeof value !== "string") {
                throw new Error("Value must come from a text input.");
              }

              await onClose(value);
            } finally {
              setLoading(false);
            }
          },
        },
      }}
    >
      <DialogTitle>{payload.title ?? "Confirm"}</DialogTitle>
      <DialogContent>
        <DialogContentText>{payload.msg} </DialogContentText>
        <TextField
          autoFocus
          required
          margin="dense"
          id="name"
          name={name}
          type="text"
          fullWidth
          variant="standard"
          value={input}
          onChange={(event) => setInput(event.target.value)}
        />
      </DialogContent>
      <DialogActions>
        <Button
          disabled={!open}
          size="small"
          variant="outlined"
          {...cancelButtonProps}
        >
          {payload.cancelText ?? "Cancel"}
        </Button>
        <Button
          disabled={!open}
          size="small"
          variant="contained"
          loading={loading}
          type="submit"
        >
          {payload.okText ?? "Ok"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

PromptDialog.propTypes = {
  /**
   * A function to call when the dialog should be closed. If the dialog has a return
   * value, it should be passed as an argument to this function. You should use the promise
   * that is returned to show a loading state while the dialog is performing async actions
   * on close.
   * @param result The result to return from the dialog.
   * @returns A promise that resolves when the dialog can be fully closed.
   */
  onClose: PropTypes.func.isRequired,
  /**
   * Whether the dialog is open.
   */
  open: PropTypes.bool.isRequired,
  /**
   * The payload that was passed when the dialog was opened.
   */
  payload: PropTypes.shape({
    cancelText: PropTypes.node,
    msg: PropTypes.node,
    okText: PropTypes.node,
    onClose: PropTypes.func,
    title: PropTypes.node,
  }).isRequired,
};

export { PromptDialog };

function ProjectPromptDialog({ open, payload, onClose }) {
  // Initialize state from initialData if provided (for edit mode)
  const initialData = payload.initialData || {};
  const isEditMode = !!initialData.id;

  const [projectName, setProjectName] = React.useState(initialData.name || "");
  const [description, setDescription] = React.useState(
    initialData.description || ""
  );
  const [tags, setTags] = React.useState(
    Array.isArray(initialData.tags)
      ? initialData.tags.join(", ")
      : typeof initialData.tags === "string"
      ? initialData.tags
      : ""
  );
  const [loading, setLoading] = React.useState(false);

  // Reset state when dialog opens with new initialData
  React.useEffect(() => {
    if (open && payload.initialData) {
      const data = payload.initialData;
      setProjectName(data.name || "");
      setDescription(data.description || "");
      setTags(
        Array.isArray(data.tags)
          ? data.tags.join(", ")
          : typeof data.tags === "string"
          ? data.tags
          : ""
      );
    } else if (open && !payload.initialData) {
      // Reset to empty for create mode
      setProjectName("");
      setDescription("");
      setTags("");
    }
  }, [open, payload.initialData]);

  const cancelButtonProps = useDialogLoadingButton(() => onClose(null));

  const PROJECT_NAME_LIMIT = 40;
  const DESCRIPTION_LIMIT = 80;

  return (
    <Dialog
      maxWidth="sm"
      fullWidth
      open={open}
      onClose={() => onClose(null)}
      slotProps={{
        paper: {
          component: "form",
          onSubmit: async (event) => {
            event.preventDefault();
            try {
              setLoading(true);

              // Validate inputs
              if (!projectName.trim()) {
                return; // Form validation will handle this
              }

              const result = {
                ...(isEditMode && { id: initialData.id }), // Include ID for edits
                name: projectName.trim(),
                description: description.trim() || "",
                tags: tags.trim()
                  ? tags
                      .split(",")
                      .map((tag) => tag.trim())
                      .filter((tag) => tag)
                  : [],
              };
              await onClose(result);
            } finally {
              setLoading(false);
            }
          },
        },
      }}
    >
      <DialogTitle>
        {payload.title ?? (isEditMode ? "Edit Project" : "Create New Project")}
      </DialogTitle>
      <DialogContent>
        <DialogContentText sx={{ mb: 2 }}>{payload.msg}</DialogContentText>

        {/* Project Name Field */}
        <Box sx={{ mb: 3 }}>
          <TextField
            autoFocus
            required
            fullWidth
            id="project-name"
            label="Project Name"
            type="text"
            variant="outlined"
            value={projectName}
            onChange={(event) => {
              const value = event.target.value;
              if (value.length <= PROJECT_NAME_LIMIT) {
                setProjectName(value);
              }
            }}
            inputProps={{
              maxLength: PROJECT_NAME_LIMIT,
            }}
            helperText={`Required field • ${projectName.length}/${PROJECT_NAME_LIMIT}`}
            FormHelperTextProps={{
              sx: {
                display: "flex",
                justifyContent: "space-between",
                color:
                  projectName.length > PROJECT_NAME_LIMIT * 0.9
                    ? "warning.main"
                    : "text.secondary",
              },
            }}
          />
        </Box>

        {/* Description Field */}
        <Box sx={{ mb: 3 }}>
          <TextField
            fullWidth
            id="project-description"
            label="Description (Optional)"
            type="text"
            variant="outlined"
            multiline
            rows={3}
            value={description || ""}
            onChange={(event) => {
              const value = event.target.value;
              if (value.length <= DESCRIPTION_LIMIT) {
                setDescription(value);
              }
            }}
            inputProps={{
              maxLength: DESCRIPTION_LIMIT,
            }}
            helperText={`Brief description of your project • ${description.length}/${DESCRIPTION_LIMIT}`}
            FormHelperTextProps={{
              sx: {
                display: "flex",
                justifyContent: "space-between",
                color:
                  description.length > DESCRIPTION_LIMIT * 0.9
                    ? "warning.main"
                    : "text.secondary",
              },
            }}
            placeholder="e.g., Gold mining feasibility study for Queensland region"
          />
        </Box>
        {/* Tags */}
        <Box sx={{ mb: 3 }}>
          <TextField
            fullWidth
            id="project-tags"
            label="Tags (Optional)"
            type="text"
            variant="outlined"
            multiline
            rows={2}
            value={tags || ""}
            onChange={(event) => {
              const value = event.target.value;
              if (value.length <= DESCRIPTION_LIMIT) {
                setTags(value);
              }
            }}
            inputProps={{
              maxLength: DESCRIPTION_LIMIT,
            }}
            helperText={`Add comma-separated tags to help organize your project • ${tags.length}/${DESCRIPTION_LIMIT}`}
            FormHelperTextProps={{
              sx: {
                display: "flex",
                justifyContent: "space-between",
                color:
                  tags.length > DESCRIPTION_LIMIT * 0.9
                    ? "warning.main"
                    : "text.secondary",
              },
            }}
            placeholder="e.g., mining, feasibility, Charlotte"
          />
        </Box>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button disabled={!open} variant="outlined" {...cancelButtonProps}>
          {payload.cancelText ?? "Cancel"}
        </Button>
        <Button
          disabled={!open || !projectName.trim()}
          variant="contained"
          loading={loading}
          type="submit"
        >
          {payload.okText ?? (isEditMode ? "Save Changes" : "Create Project")}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
ProjectPromptDialog.propTypes = {
  /**
   * A function to call when the dialog should be closed. If the dialog has a return
   * value, it should be passed as an argument to this function. You should use the promise
   * that is returned to show a loading state while the dialog is performing async actions
   * on close.
   * @param result The result to return from the dialog.
   * @returns A promise that resolves when the dialog can be fully closed.
   */
  onClose: PropTypes.func.isRequired,
  /**
   * Whether the dialog is open.
   */
  open: PropTypes.bool.isRequired,
  /**
   * The payload that was passed when the dialog was opened.
   */
  payload: PropTypes.shape({
    cancelText: PropTypes.node,
    msg: PropTypes.node,
    okText: PropTypes.node,
    onClose: PropTypes.func,
    title: PropTypes.node,
    initialData: PropTypes.shape({
      id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
      name: PropTypes.string,
      description: PropTypes.string,
      tags: PropTypes.oneOfType([
        PropTypes.arrayOf(PropTypes.string),
        PropTypes.string,
      ]),
    }),
  }).isRequired,
};

export { ProjectPromptDialog };

function ClearDataDialog({ open, payload, onClose }) {
  const cancelButtonProps = useDialogLoadingButton(() => onClose(false));
  const confirmButtonProps = useDialogLoadingButton(() => onClose(true));

  return (
    <Dialog open={open} onClose={() => onClose(false)} maxWidth="sm" fullWidth>
      <DialogTitle sx={{ display: "flex", alignItems: "center" }}>
        <Warning sx={{ mr: 1, color: "error.main" }} />
        {payload.title ?? "Clear All Data"}
      </DialogTitle>
      <DialogContent>
        <DialogContentText>
          <strong>Warning:</strong>{" "}
          {payload.warningMsg ??
            "This action will permanently delete ALL data associated with the document, including:"}
        </DialogContentText>
        {/* <Box component="ul" sx={{ mt: 2, mb: 2 }}>
                    <li>All projects and documents</li>
                    <li>All uploaded files and extracted data</li>
                    <li>All user-generated content</li>
                    <li>All processing history</li>
                </Box> */}
        <DialogContentText color="error">
          {payload.msg ??
            "This action cannot be undone. Are you absolutely sure?"}
        </DialogContentText>
      </DialogContent>
      <DialogActions>
        <Button disabled={!open} {...cancelButtonProps}>
          {payload.cancelText ?? "Cancel"}
        </Button>
        <Button
          color="error"
          variant="contained"
          disabled={!open}
          {...confirmButtonProps}
          startIcon={
            confirmButtonProps.loading ? (
              <CircularProgress size={16} />
            ) : (
              <DeleteSweep />
            )
          }
        >
          {confirmButtonProps.loading
            ? "Clearing..."
            : payload.okText ?? "Clear All Data"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

ClearDataDialog.propTypes = {
  onClose: PropTypes.func.isRequired,
  open: PropTypes.bool.isRequired,
  payload: PropTypes.shape({
    cancelText: PropTypes.node,
    msg: PropTypes.node,
    warningMsg: PropTypes.node,
    okText: PropTypes.node,
    title: PropTypes.node,
  }).isRequired,
};

export { ClearDataDialog };

// Dialog to delete a project and its data
function ProjectDeleteDialog({ open, payload, onClose }) {
  const cancelButtonProps = useDialogLoadingButton(() => onClose(false));
  const deleteButtonProps = useDialogLoadingButton(() => onClose(true));

  return (
    <Dialog maxWidth="xs" fullWidth open={open} onClose={() => onClose(false)}>
      <DialogTitle>Delete Project</DialogTitle>
      <DialogContent>
        <DialogContentText>
          Are you sure you want to delete the project "{payload.projectName}"?
          This action cannot be undone.
        </DialogContentText>
      </DialogContent>
      <DialogActions>
        <Button disabled={!open} {...cancelButtonProps}>
          Cancel
        </Button>
        <Button color="error" disabled={!open} {...deleteButtonProps}>
          Delete
        </Button>
      </DialogActions>
    </Dialog>
  );
}

ProjectDeleteDialog.propTypes = {
  onClose: PropTypes.func.isRequired,
  open: PropTypes.bool.isRequired,
  payload: PropTypes.shape({
    projectName: PropTypes.string.isRequired,
  }).isRequired,
};

export { ProjectDeleteDialog };

export function useDialogs() {
  const dialogsContext = React.useContext(DialogsContext);
  if (!dialogsContext) {
    throw new Error("Dialogs context was used without a provider.");
  }
  const { open, close } = dialogsContext;

  const alert = useEventCallback((msg, { onClose, ...options } = {}) =>
    open(AlertDialog, { ...options, msg }, { onClose })
  );

  const confirm = useEventCallback((msg, { onClose, ...options } = {}) =>
    open(ConfirmDialog, { ...options, msg }, { onClose })
  );

  const prompt = useEventCallback((msg, { onClose, ...options } = {}) =>
    open(PromptDialog, { ...options, msg }, { onClose })
  );

  const clearData = useEventCallback((msg, { onClose, ...options } = {}) =>
    open(ClearDataDialog, { ...options, msg }, { onClose })
  );

  // New project prompt with description support
  const projectPrompt = useEventCallback((msg, { onClose, ...options } = {}) =>
    open(ProjectPromptDialog, { ...options, msg }, { onClose })
  );

  return React.useMemo(
    () => ({
      alert,
      confirm,
      prompt,
      projectPrompt,
      clearData,
      open,
      close,
    }),
    [alert, close, confirm, open, prompt, projectPrompt, clearData]
  );
}

// HMR acceptance
if (module.hot) {
  module.hot.accept();
}
