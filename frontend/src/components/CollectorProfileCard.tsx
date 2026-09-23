import {
  useEffect,
  useState,
} from "react";

import {
  fetchCollectorProfile,
  saveCollectorProfile,
  type CollectorAgeGroup,
  type CollectorDominantHand,
  type CollectorGender,
  type CollectorProfileUpdate,
  type CollectorSourceType,
} from "../services/api";


type Props = {
  signerId: string;
  disabled?: boolean;
};


const EMPTY_PROFILE:
  CollectorProfileUpdate = {
    source_type: "other",

    age_group:
      "unspecified",

    gender:
      "unspecified",

    dominant_hand:
      "unspecified",

    consent_confirmed:
      false,

    note: "",
  };


export function CollectorProfileCard(
  {
    signerId,
    disabled = false,
  }: Props
) {
  const [
    profile,
    setProfile,
  ] =
    useState<
      CollectorProfileUpdate
    >(
      EMPTY_PROFILE
    );


  const [
    exists,
    setExists,
  ] =
    useState(false);


  const [
    loading,
    setLoading,
  ] =
    useState(false);


  const [
    saving,
    setSaving,
  ] =
    useState(false);


  const [
    message,
    setMessage,
  ] =
    useState("");


  const normalized =
    signerId
      .trim()
      .toUpperCase();


  const valid =
    /^S\d{3,}$/.test(
      normalized
    );


  useEffect(() => {
    if (!valid) {
      setProfile({
        ...EMPTY_PROFILE,
      });

      setExists(false);

      setMessage("");

      return;
    }


    let cancelled =
      false;


    async function load() {
      try {
        setLoading(true);

        setMessage("");

        const response =
          await fetchCollectorProfile(
            normalized
          );


        if (cancelled) {
          return;
        }


        setExists(
          response.exists
        );


        setProfile({
          source_type:
            response
              .profile
              .source_type,

          age_group:
            response
              .profile
              .age_group,

          gender:
            response
              .profile
              .gender,

          dominant_hand:
            response
              .profile
              .dominant_hand,

          consent_confirmed:
            response
              .profile
              .consent_confirmed,

          note:
            response
              .profile
              .note,
        });
      }
      catch (error) {
        if (!cancelled) {
          setMessage(
            error instanceof Error
              ?
                error.message
              :
                "读取采集者档案失败。"
          );
        }
      }
      finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }


    void load();


    return () => {
      cancelled = true;
    };
  }, [
    normalized,
    valid,
  ]);


  async function handleSave() {
    if (!valid) {
      return;
    }


    try {
      setSaving(true);

      setMessage("");


      await saveCollectorProfile(
        normalized,
        profile
      );


      setExists(true);


      setMessage(
        "采集者档案已保存 ✓"
      );
    }
    catch (error) {
      setMessage(
        error instanceof Error
          ?
            error.message
          :
            "保存采集者档案失败。"
      );
    }
    finally {
      setSaving(false);
    }
  }


  function updateSourceType(
    value: string
  ) {
    setProfile(
      (current) => ({
        ...current,

        source_type:
          value as CollectorSourceType,
      })
    );
  }


  function updateAgeGroup(
    value: string
  ) {
    setProfile(
      (current) => ({
        ...current,

        age_group:
          value as CollectorAgeGroup,
      })
    );
  }


  function updateGender(
    value: string
  ) {
    setProfile(
      (current) => ({
        ...current,

        gender:
          value as CollectorGender,
      })
    );
  }


  function updateDominantHand(
    value: string
  ) {
    setProfile(
      (current) => ({
        ...current,

        dominant_hand:
          value as CollectorDominantHand,
      })
    );
  }


  if (!valid) {
    return (
      <div className="collector-profile-card">

        <div className="collector-profile-header">
          <div>
            <strong>
              采集者档案
            </strong>

            <span>
              Signer Profile
            </span>
          </div>
        </div>


        <span className="danger-text">
          请先输入有效的 Signer ID，
          例如 S001。
        </span>

      </div>
    );
  }


  return (
    <div className="collector-profile-card">

      <div className="collector-profile-header">

        <div>
          <strong>
            采集者档案 · {
              normalized
            }
          </strong>

          <span>
            {
              loading
                ?
                  "正在读取…"
                :
                  exists
                    ?
                      "已建立档案"
                    :
                      "尚未建立档案"
            }
          </span>
        </div>


        <button
          type="button"
          className="secondary-button"
          disabled={
            disabled ||
            loading ||
            saving
          }
          onClick={() =>
            void handleSave()
          }
        >
          {
            saving
              ?
                "保存中…"
              :
                "保存档案"
          }
        </button>

      </div>


      <div className="collector-profile-grid">

        <label>

          <span>
            数据来源
          </span>

          <select
            value={
              profile.source_type
            }
            disabled={
              disabled
            }
            onChange={(
              event
            ) =>
              updateSourceType(
                event
                  .target
                  .value
              )
            }
          >

            <option
              value="team_member"
            >
              团队成员
            </option>

            <option
              value="friend_or_roommate"
            >
              朋友 / 室友
            </option>

            <option
              value="volunteer"
            >
              志愿采集者
            </option>

            <option
              value="other"
            >
              其他
            </option>

          </select>

        </label>


        <label>

          <span>
            年龄段
          </span>

          <select
            value={
              profile.age_group
            }
            disabled={
              disabled
            }
            onChange={(
              event
            ) =>
              updateAgeGroup(
                event
                  .target
                  .value
              )
            }
          >

            <option
              value="unspecified"
            >
              未记录
            </option>

            <option
              value="under_18"
            >
              18 岁以下
            </option>

            <option
              value="18_25"
            >
              18–25
            </option>

            <option
              value="26_40"
            >
              26–40
            </option>

            <option
              value="41_60"
            >
              41–60
            </option>

            <option
              value="60_plus"
            >
              60 岁以上
            </option>

          </select>

        </label>


        <label>

          <span>
            性别
          </span>

          <select
            value={
              profile.gender
            }
            disabled={
              disabled
            }
            onChange={(
              event
            ) =>
              updateGender(
                event
                  .target
                  .value
              )
            }
          >

            <option
              value="unspecified"
            >
              未记录
            </option>

            <option
              value="male"
            >
              男
            </option>

            <option
              value="female"
            >
              女
            </option>

            <option
              value="other"
            >
              其他
            </option>

            <option
              value="prefer_not_to_say"
            >
              不愿说明
            </option>

          </select>

        </label>


        <label>

          <span>
            优势手
          </span>

          <select
            value={
              profile.dominant_hand
            }
            disabled={
              disabled
            }
            onChange={(
              event
            ) =>
              updateDominantHand(
                event
                  .target
                  .value
              )
            }
          >

            <option
              value="unspecified"
            >
              未记录
            </option>

            <option
              value="right"
            >
              右手
            </option>

            <option
              value="left"
            >
              左手
            </option>

            <option
              value="both"
            >
              双手 / 无明显优势
            </option>

          </select>

        </label>

      </div>


      <label className="collector-note-field">

        <span>
          来源 / 采集备注
        </span>

        <textarea
          value={
            profile.note
          }
          disabled={
            disabled
          }
          maxLength={
            1000
          }
          rows={
            3
          }
          placeholder={
            "例如：团队成员；第一批室内采集；佩戴眼镜；宿舍自然光。不要填写真实姓名、手机号、学号等直接身份信息。"
          }
          onChange={(
            event
          ) =>
            setProfile(
              (current) => ({
                ...current,

                note:
                  event
                    .target
                    .value,
              })
            )
          }
        />

        <small>
          {
            profile.note.length
          }
          {" / 1000"}
        </small>

      </label>


      <label className="collector-consent-field">

        <input
          type="checkbox"
          checked={
            profile
              .consent_confirmed
          }
          disabled={
            disabled
          }
          onChange={(
            event
          ) =>
            setProfile(
              (current) => ({
                ...current,

                consent_confirmed:
                  event
                    .target
                    .checked,
              })
            )
          }
        />


        <span>
          已确认采集者知情并同意将本次匿名关键点数据用于项目训练、测试与比赛展示。
        </span>

      </label>


      {message && (
        <div className="collector-profile-message">
          {message}
        </div>
      )}

    </div>
  );
}
