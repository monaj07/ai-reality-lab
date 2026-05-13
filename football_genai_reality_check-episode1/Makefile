.PHONY: eval ask notebook

eval:
	PYTHONPATH=src python scripts/evaluate.py --agent both --backend mock --out-dir reports

ask:
	PYTHONPATH=src python scripts/ask.py "Did Italy qualify for the 2026 FIFA World Cup?" --agent grounded --backend mock

notebook:
	PYTHONPATH=src jupyter nbconvert --to notebook --execute notebooks/01_world_cup_agent_reality_check.ipynb --output 01_world_cup_agent_reality_check.executed.ipynb

validate-groups:
	PYTHONPATH=src python scripts/validate_groups.py
