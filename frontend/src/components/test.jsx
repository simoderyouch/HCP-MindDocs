import DocViewer, { DocViewerRenderers } from "@cyntler/react-doc-viewer";

export default function Viewer({url , file}) {
  const docs = [
    { uri: url ,
        fileType : file.file_type.toLowerCase(),
        fileName : file.file_name
    }, 
   
  ];

  return <DocViewer documents={docs} pluginRenderers={DocViewerRenderers} />;
}