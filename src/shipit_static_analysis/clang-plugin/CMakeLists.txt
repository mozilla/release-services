set(LLVM_LINK_COMPONENTS support)

add_definitions( -DCLANG_TIDY )
add_definitions( -DHAVE_NEW_ASTMATCHER_NAMES )

add_clang_library(clangTidyMozillaModule
	ArithmeticArgChecker.cpp
	AssertAssignmentChecker.cpp
	CanRunScriptChecker.cpp
	CustomTypeAnnotation.cpp
	DanglingOnTemporaryChecker.cpp
	DiagnosticsMatcher.cpp
	ExplicitImplicitChecker.cpp
	ExplicitOperatorBoolChecker.cpp
	KungFuDeathGripChecker.cpp
	MozCheckAction.cpp
	MozillaTidyModule.cpp
	MustOverrideChecker.cpp
	MustReturnFromCallerChecker.cpp
	MustUseChecker.cpp
	NaNExprChecker.cpp
	NeedsNoVTableTypeChecker.cpp
	NoAddRefReleaseOnReturnChecker.cpp
	NoAutoTypeChecker.cpp
	NoDuplicateRefCntMemberChecker.cpp
	NoExplicitMoveConstructorChecker.cpp
	NonMemMovableMemberChecker.cpp
	NonMemMovableTemplateArgChecker.cpp
	NonParamInsideFunctionDeclChecker.cpp
	OverrideBaseCallChecker.cpp
	OverrideBaseCallUsageChecker.cpp
	RefCountedCopyConstructorChecker.cpp
	RefCountedInsideLambdaChecker.cpp
	ScopeChecker.cpp
	SprintfLiteralChecker.cpp
	TrivialCtorDtorChecker.cpp
	VariableUsageHelpers.cpp

  LINK_LIBS
  clangAST
  clangASTMatchers
  clangBasic
  clangLex
  clangTidy
  clangTidyReadabilityModule
  clangTidyUtils
  )
