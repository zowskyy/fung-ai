extends Node

signal scene_finished(success: bool, message: String)

const CAVE_WORLD_PATH := "res://examples/cave_boss/cave_world.json"
const ENTITY_PATH := "res://examples/cave_boss/cave_boss_entity.json"
const ENCOUNTER_PATH := "res://examples/cave_boss/cave_encounter.json"
const NARRATIVE_PATH := "res://examples/cave_boss/narrative_sequence.json"
const ANIMATION_MANIFEST_PATH := "res://examples/cave_boss/animation_manifest.json"
const REPLAY_OUTPUT_PATH := "res://examples/cave_boss/replay.json"

var _save_service := SaveService.new()
var _replay_recorder := ReplayRecorder.new()
var _snapshot_serializer := SnapshotSerializer.new()
var _entity_registry := EntityRegistry.new()
var _spawn_service := SpawnService.new()
var _archetype_db := ArchetypeDatabase.new()
var _cutscene_director := CutsceneDirector.new()
var _animation_controller := AnimationController.new()
var _world_job: WorldGenerationJob

var _world_state: WorldState
var _entity_data: Dictionary
var _encounter_data: Dictionary
var _seed: int = 42
var _finished_called := false
var _schema_validator := SchemaValidationExample.new()


func _ready() -> void:
	add_child(_cutscene_director)
	add_child(_animation_controller)

	_cutscene_director.beat_started.connect(_on_beat_started)
	_cutscene_director.choice_requested.connect(_on_choice_requested)
	_cutscene_director.finished.connect(_on_narrative_finished)

	var has_seed_arg := false
	for arg in OS.get_cmdline_args():
		if arg.begins_with("--seed="):
			has_seed_arg = true
			_seed = int(arg.substr("--seed=".length()))

	_world_job = WorldGenerationJob.new()
	_world_job.completed.connect(_on_world_completed)
	_world_job.failed.connect(_on_world_failed)

	if has_seed_arg:
		_world_job.start({"seed": _seed, "width": 5, "height": 5})
	else:
		_world_job.start({"world_json_path": CAVE_WORLD_PATH})


func _on_world_failed(error: String) -> void:
	push_error("WorldGenerationJob failed: %s" % error)
	notify_finished(false, "World generation failed: %s" % error)


func _on_world_completed(result: Dictionary) -> void:
	print("[main] World generation completed")
	_replay_recorder.start(result.get("seed", _seed))
	_replay_recorder.record_action("world_generated", {"world_id": result.get("id", "")})

	print("[main] Loading world state...")
	_world_state = WorldLoader.new().load_world(result, self)
	if _world_state == null:
		push_error("[main] WorldLoader failed")
		notify_finished(false, "WorldLoader failed to build WorldState from generated result")
		return
	print("[main] World state loaded successfully")
	_replay_recorder.advance_frame()
	_replay_recorder.record_action("world_loaded")

	print("[main] Loading entity and encounter data...")
	_entity_data = _save_service.load_json(ENTITY_PATH)
	_encounter_data = _save_service.load_json(ENCOUNTER_PATH)
	if _entity_data.is_empty() or _encounter_data.is_empty():
		push_error("[main] Failed to load entity or encounter data")
		notify_finished(false, "Failed to load entity or encounter data")
		return
	print("[main] Entity and encounter data loaded")

	# Validate loaded data against schemas
	print("[main] Validating loaded data against JSON Schema contracts...")
	var validation_result := _schema_validator.validate_world_data()
	if not validation_result.success:
		push_error("[main] Schema validation failed: %s" % validation_result.errors)
		notify_finished(false, "Schema validation failed: %s" % ", ".join(validation_result.errors))
		return
	print("[main] Schema validation passed for world data")

	print("[main] Loading animation manifest...")
	var manifest_data := _save_service.load_json(ANIMATION_MANIFEST_PATH)
	var manifest_index := AnimationManifestLoader.new().load_from_dict(manifest_data)
	_animation_controller.load_manifest(manifest_index)
	print("[main] Animation manifest loaded")

	print("[main] Spawning encounter...")
	var spawner := EncounterSpawner.new()
	add_child(spawner)
	spawner.encounter_triggered.connect(_on_encounter_triggered)
	spawner.spawn(_encounter_data, _entity_data, _world_state, _entity_registry, _spawn_service, _archetype_db)
	_replay_recorder.advance_frame()
	_replay_recorder.record_action("encounter_spawned", {"encounter_id": _encounter_data.get("id", "")})
	print("[main] Encounter spawned successfully")


func _on_encounter_triggered(encounter_id: String, narrative_id: String) -> void:
	if narrative_id.is_empty():
		notify_finished(false, "Encounter '%s' has no linked narrative_id" % encounter_id)
		return

	var narrative_data := _save_service.load_json(NARRATIVE_PATH)
	if narrative_data.is_empty():
		notify_finished(false, "Failed to load narrative data")
		return

	_replay_recorder.advance_frame()
	_replay_recorder.record_action("narrative_started", {"sequence_id": narrative_data.get("sequence_id", "")})
	_cutscene_director.play(narrative_data, {"chose_fight": true})


func _on_beat_started(beat: Dictionary) -> void:
	if beat.get("type", "") == "animation_cue":
		_animation_controller.play(beat.get("animation_id", ""))
		_replay_recorder.advance_frame()
		_replay_recorder.record_action("animation_played", {"animation_id": beat.get("animation_id", "")})


func _on_choice_requested(beat: Dictionary) -> void:
	var options: Array = beat.get("options", [])
	if options.is_empty():
		return
	# Headless runs are non-interactive, so the first offered option is
	# always taken deterministically.
	var option_id: String = options[0].get("id", "")
	_replay_recorder.advance_frame()
	_replay_recorder.record_action("choice", {"beat_id": beat.get("id", ""), "option_id": option_id})
	_cutscene_director.resolve_choice(option_id)


func _on_narrative_finished(sequence_id: String) -> void:
	_replay_recorder.advance_frame()
	_replay_recorder.record_action("narrative_finished", {"sequence_id": sequence_id})

	var entities: Array = []
	var boss_node := _entity_registry.get_entity(_entity_data.get("id", ""))
	if boss_node != null:
		entities.append({
			"id": boss_node.get_meta("entity_id", ""),
			"health": boss_node.get_meta("health", 0),
			"tags": boss_node.get_meta("tags", []),
		})

	var world_snapshot := {
		"id": _world_state.id,
		"seed": _world_state.seed,
		"width": _world_state.width,
		"height": _world_state.height,
	}
	var flags := {"chose_fight": true}
	var snapshot := _snapshot_serializer.serialize(world_snapshot, entities, flags)

	_replay_recorder.record_action("finish")
	var replay := _replay_recorder.finish(snapshot)

	var err := _save_service.save_json(REPLAY_OUTPUT_PATH, replay)
	if err != OK:
		notify_finished(false, "Failed to write replay.json: %s" % error_string(err))
		return

	notify_finished(true, "Vertical slice completed successfully")


func notify_finished(success: bool, message: String) -> void:
	if _finished_called:
		return
	_finished_called = true
	scene_finished.emit(success, message)
