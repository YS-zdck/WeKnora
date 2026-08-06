package docparser

import (
	"testing"

	"github.com/Tencent/WeKnora/internal/types"
)

func TestListAllEnginesBuiltinIncludesHTML(t *testing.T) {
	engines := ListAllEngines(true, nil, nil)
	for _, engine := range engines {
		if engine.Name != "builtin" {
			continue
		}
		if !engine.Available {
			t.Fatalf("builtin engine is unavailable: %s", engine.UnavailableReason)
		}

		fileTypes := make(map[string]bool, len(engine.FileTypes))
		for _, fileType := range engine.FileTypes {
			fileTypes[fileType] = true
		}
		for _, want := range []string{"html", "htm"} {
			if !fileTypes[want] {
				t.Errorf("builtin engine file types do not include %q: %v", want, engine.FileTypes)
			}
		}
		return
	}

	t.Fatal("builtin engine not found")
}

func TestListAllEnginesIncludesRemotePDFInspector(t *testing.T) {
	remote := []types.ParserEngineInfo{{
		Name:              "pdf_inspector",
		Description:       "PDF Inspector",
		FileTypes:         []string{"pdf"},
		Available:         false,
		UnavailableReason: "missing package",
	}}

	engines := ListAllEngines(true, nil, remote)
	for _, engine := range engines {
		if engine.Name != "pdf_inspector" {
			continue
		}
		if engine.Available {
			t.Fatal("pdf_inspector availability was not preserved")
		}
		if engine.UnavailableReason != "missing package" {
			t.Fatalf("unexpected unavailable reason: %q", engine.UnavailableReason)
		}
		if len(engine.FileTypes) != 1 || engine.FileTypes[0] != "pdf" {
			t.Fatalf("unexpected file types: %v", engine.FileTypes)
		}
		return
	}

	t.Fatal("remote pdf_inspector engine not found")
}
